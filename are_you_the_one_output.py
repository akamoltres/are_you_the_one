
import openpyxl

def generate_probability_table(total_valid, constraints, pair_count):
    probability_table = []
    probability_table.append([i for i in constraints["men"]])
    probability_table[0].insert(0, "")
    for idx, i in enumerate(pair_count):
        probability_table.append([constraints["women"][idx]])
        for j in i:
            if j == 0:
                probability_table[idx + 1].append("X")
            elif j == total_valid:
                probability_table[idx + 1].append("MATCH")
            else:
                probability_table[idx + 1].append("{:.2f}%".format(float(j) / float(total_valid) * 100.0))
    return probability_table

def write_to_csv(filename):
    pass

def write_to_xlsx(filename):
    pass
