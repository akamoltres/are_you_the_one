#!/bin/python3

from are_you_the_one_output import generate_probability_table, write_to_xlsx
import argparse
import os
import sys
from tabulate import tabulate
import toml

class Pair:
    def __init__(self, man_idx, woman_idx):
        self.man_idx = man_idx
        self.woman_idx = woman_idx

def check_matchup(men, women, pairs, correct_count, women_assigned):
    possibility_count = 0
    for p in pairs:
        if women_assigned[p.woman_idx] == p.man_idx:
            possibility_count += 1
            if possibility_count > correct_count:
                return False
    return (possibility_count == correct_count)

def check_booth(men, women, booth, booth_status, women_assigned):
    for i,b in enumerate(booth):
        if booth_status[i] == "yes":
            return women_assigned[b.woman_idx] == b.man_idx
        elif booth_status[i] == "no":
            return women_assigned[b.woman_idx] != b.man_idx
        else:
            assert False

def check_week(week, constraints, women_assigned):
    week = f"week{week}"
    return (check_matchup(
                constraints["men"],
                constraints["women"],
                constraints[week]["pairs"],
                constraints[week]["correct"],
                women_assigned) and 
            check_booth(
                constraints["men"],
                constraints["women"],
                constraints[week]["booth"],
                constraints[week]["booth_status"],
                women_assigned))

def is_possibility(week, phase, constraints, women_assigned, pair_count):
    for w in range(1, week):
        if not check_week(w, constraints, women_assigned):
            return False
    if phase == "b":
        return check_week(week, constraints, women_assigned)
    else:
        return check_booth(
                   constraints["men"],
                   constraints["women"],
                   constraints[f"week{week}"]["booth"],
                   constraints[f"week{week}"]["booth_status"],
                   women_assigned)

def count(depth, week, phase, constraints, women_assigned, pair_count):
    if depth == len(constraints["men"]):
        valid = is_possibility(week, phase, constraints, women_assigned, pair_count)
        if valid:
            for idx, i in enumerate(women_assigned):
                pair_count[idx][i] += 1
        return valid

    total_valid = 0

    for i in range(len(women_assigned)):
        if women_assigned[i] == -1:
            # continue searching
            women_assigned[i] = depth
            total_valid += count(depth + 1, week, phase, constraints, women_assigned, pair_count)
            women_assigned[i] = -1

    return total_valid

def pair_to_Pair(pair, men_list, women_list):
    assert len(pair) == 2
    assert (pair[0] in men_list and pair[1] in women_list) or (pair[0] in women_list and pair[1] in men_list)

    man_name = ""
    woman_name = ""
    man_idx = ""
    woman_idx = ""

    if pair[0] in men_list:
        man_name = pair[0]
        woman_name = pair[1]
    elif pair[0] in women_list:
        woman_name = pair[0]
        man_name = pair[1]

    man_idx = men_list.index(man_name)
    woman_idx = women_list.index(woman_name)

    return Pair(man_idx, woman_idx)

# input toml has pairs as lists
# convert these lists to Pair objects to speed up lookups
def pairs_to_Pairs(constraints):
    men_list = constraints["men"]
    women_list = constraints["women"]
    for w in range(1, int(constraints["weeks"]) + 1):
        # setup
        week = f"week{w}"

        # convert the truth booth pairs
        booth_list_Pairs = list()
        if not isinstance(constraints[week]["booth"][0], list):
            constraints[week]["booth"] = [constraints[week]["booth"]]
            constraints[week]["booth_status"] = [constraints[week]["booth_status"]]
        for b in constraints[week]["booth"]:
            booth_list_Pairs.append(pair_to_Pair(b, men_list, women_list))
        constraints[week]["booth"] = booth_list_Pairs

        # convert the matchup ceremony pairs
        for idx, pair in enumerate(constraints[week]["pairs"]):
            constraints[week]["pairs"][idx] = pair_to_Pair(pair, men_list, women_list)

def main(args):
    constraint_file = os.path.join("constraints", f"s{args.season}.toml")

    # validate season
    assert os.path.isfile(constraint_file)

    # load constraints
    constraints = None
    with open(constraint_file, "r") as fin:
        constraints = toml.load(fin)

    # validate week
    assert (1 <= args.week <= int(constraints["weeks"]))

    # rebuild constraint data
    num_men = len(constraints["men"])
    num_women = len(constraints["women"])
    pairs_to_Pairs(constraints)

    # initialization
    women_assigned = [-1] * num_women
    pair_count = [[0 for i in range(num_women)] for j in range(num_men)]

    # try every matchup configuration and generate probabilities
    total_valid = count(0, args.week, args.phase, constraints, women_assigned, pair_count)
    probability_table = generate_probability_table(total_valid, constraints, pair_count)

    # console output
    print(f"Remaining configurations: {total_valid}")
    print(tabulate(probability_table))

    # reload constraints
    constraints = None
    with open(constraint_file, "r") as fin:
        constraints = toml.load(fin)

    # file output
    if args.xlsx is not None:
        filename = args.xlsx[0] + ".xlsx"
        write_to_xlsx(filename, total_valid, probability_table, constraints, args.week, args.phase)

if __name__ == "__main__":
    # handle arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("season", help = "season to analyze", type = int)
    parser.add_argument("week", help = "week to analyze", type = int)
    parser.add_argument("phase", help = "a for after the truth booth, b for after the matchup ceremony", choices = ("a", "b"))
    parser.add_argument("--xlsx", help = "write output to excel 2010 file", nargs = 1)
    args = parser.parse_args()

    # enter program
    main(args)
