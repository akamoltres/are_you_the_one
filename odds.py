
from copy import deepcopy
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
    if booth_status == "yes":
        return women_assigned[booth.woman_idx] == booth.man_idx
    elif booth_status == "no":
        return women_assigned[booth.woman_idx] != booth.man_idx
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
        week = "week{}".format(w)

        # convert the truth booth pairs
        constraints[week]["booth"] = pair_to_Pair(constraints[week]["booth"], men_list, women_list)

        # convert the matchup ceremony pairs
        for idx, pair in enumerate(constraints[week]["pairs"]):
            constraints[week]["pairs"][idx] = pair_to_Pair(pair, men_list, women_list)

def main(season, week, phase):
    constraint_file = os.path.join("constraints", "s{}.toml".format(season))

    # verify that the season's input file exists
    assert os.path.isfile(constraint_file)

    # load constraints
    constraints = None
    with open(constraint_file, "r") as fin:
        constraints = toml.load(fin)

    # validate inputs
    assert (1 <= week <= int(constraints["weeks"]))
    assert (phase == "a" or phase == "b")

    # rebuild constraint data
    num_men = len(constraints["men"])
    num_women = len(constraints["women"])
    pairs_to_Pairs(constraints)

    # initialization
    women_assigned = [-1] * num_women
    pair_count = [[0 for i in range(num_men)] for j in range(num_women)]

    # try every matchup configuration
    total_valid = count(0, week, phase, constraints, women_assigned, pair_count)

    # build the output probabilities table
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

    print("Remaining configurations: {}".format(total_valid))
    print(tabulate(transposed))

if __name__ == "__main__":
    if sys.argv[1] == "-h" or sys.argv[1] == "--help" or sys.argv[1] == "help":
        print("first argument is season")
        print("second argument is week")
        print("third argument is phase (a for after truth booth, b for after matchups)")

    else:
        assert len(sys.argv) == 4
        main(int(sys.argv[1]), int(sys.argv[2]), sys.argv[3])
