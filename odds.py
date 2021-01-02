
from copy import deepcopy
import os
import sys
from tabulate import tabulate
import toml

def check_matchup(men, women, pairs, correct_count, women_assigned):
    possibility_count = 0
    for i in range(len(women_assigned)):
        man_name = men[women_assigned[i]]
        woman_name = women[i]
        for j in pairs:
            if (j[0] == man_name and j[1] == woman_name) or (j[0] == woman_name and j[1] == man_name):
                possibility_count += 1
            if possibility_count > correct_count:
                return False
    return (possibility_count == correct_count)

def check_booth(men, women, booth, booth_status, women_assigned):
    booth_man = 0
    booth_woman = 1
    if booth[0] in women:
        booth_man = 1
        booth_woman = 0
    match = (booth[booth_man] == men[women_assigned[women.index(booth[booth_woman])]])
    if booth_status == "yes":
        return match
    elif booth_status == "no":
        return not match
    assert False

def check_week(week, constraints, women_assigned):
    week = "week{}".format(week)
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
                   constraints["week{}".format(week)]["booth"],
                   constraints["week{}".format(week)]["booth_status"],
                   women_assigned)

def count(depth, week, phase, constraints, women_assigned, pair_count):
    if depth == len(constraints["men"]):
        valid = is_possibility(week, phase, constraints, women_assigned, pair_count)
        if valid:
            for idx, i in enumerate(women_assigned):
                pair_count[i][idx] += 1
        return valid

    total_valid = 0

    for i in range(len(women_assigned)):
        if women_assigned[i] == -1:
            # continue searching
            women_assigned[i] = depth
            total_valid += count(depth + 1, week, phase, constraints, women_assigned, pair_count)
            women_assigned[i] = -1

    return total_valid

def main(season, week, phase):
    constraint_file = os.path.join("constraints", "s{}.toml".format(season))

    # verify that the season's input file exists
    assert os.path.isfile(constraint_file)

    constraints = None
    with open(constraint_file, "r") as fin:
        constraints = toml.load(fin)

    assert (1 <= week <= int(constraints["weeks"]))
    assert (phase == "a" or phase == "b")

    num_men = len(constraints["men"])
    num_women = len(constraints["women"])

    women_assigned = [-1] * num_women

    pair_count = [[0 for i in range(num_men)] for j in range(num_women)]

    total_valid = count(0, week, phase, constraints, women_assigned, pair_count)

    output_table = []
    output_table.append([i for i in constraints["women"]])
    output_table[0].insert(0, "")
    for idx, i in enumerate(pair_count):
        output_table.append([constraints["men"][idx]])
        for j in i:
            if j == 0:
                output_table[idx + 1].append("X")
            elif j == total_valid:
                output_table[idx + 1].append("MATCH")
            else:
                output_table[idx + 1].append("{:.2f}%".format(float(j) / float(total_valid) * 100.0))

    # transpose to match areuthe.blogspot.com
    transposed = deepcopy(output_table)
    for i in range(len(output_table)):
        for j in range(len(output_table[i])):
            transposed[j][i] = output_table[i][j]

    print(total_valid)
    print(tabulate(transposed))

if __name__ == "__main__":
    if sys.argv[1] == "-h" or sys.argv[1] == "--help" or sys.argv[1] == "help":
        print("first argument is season")
        print("second argument is week")
        print("third argument is phase (a for after truth booth, b for after matchups)")

    else:
        assert len(sys.argv) == 4
        main(int(sys.argv[1]), int(sys.argv[2]), sys.argv[3])
