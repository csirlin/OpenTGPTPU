# run all squishtests

import os
import tests
from test_utils import ParamHandler
import sys
import json
import time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

# add base folder (OPENTGPTPU) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from config import HAZARD_DETECTION, UB_ADDR_SIZE

# maps an (instr1_instr2) pair to:
#   the parametrized squishtest to call 
#   the valid setup RW counts
#   the parametrized vars (possible vars are l1, l2, hm2, ub2, and acc2)
#   flags on instr1 and instr2 (currently just used for MMC.S)

#   no flag because RHM.S is hardcoded in the test. unlike MMC/MMC.S, RHM/RHM.S
#   are completely different instructions and have separate tests.

#   if a test doesn't use l1 or l2, they default to 0 in terms of their use as
#   a variable. but they default to 1 in terms of hm2, ub2, and acc2 placements.
#   this allows for RHM.S X X 0 instructions, which have a literal length of 0
#   but function as though their length is 1. 
info_map = {
    "rhm_rhm":   {"func": tests.rhm_rhm,   "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l1", "l2", "hm2", "ub2"]},
    "rhm_rhms":  {"func": tests.rhm_rhms,  "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l1", "hm2", "ub2", "col"], "argl2": 0}, 
    "rhm_rhmv":  {"func": tests.rhm_rhms,  "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l1", "l2", "hm2", "ub2", "col"]}, 
    "rhm_rhmc":  {"func": tests.rhm_rhmc,  "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l1", "ub2"]},
    "rhm_whm":   {"func": tests.rhm_whm,   "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l1", "l2", "hm2", "ub2"]},
    "rhm_rw":    {"func": tests.rhm_rw,    "setup_rw_cts": [0, 1, 2, 3   ], "vars": ["l1"]},
    "rhm_mmc":   {"func": tests.rhm_mmc,   "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l1", "l2", "ub2"]},
    "rhm_mmcs":  {"func": tests.rhm_mmc,   "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l1", "l2", "ub2"], "flag2": "S"},
    "rhm_act":   {"func": tests.rhm_act,   "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l1", "l2", "ub2"]},
    "rhm_hlt":   {"func": tests.rhm_hlt,   "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l1"]},

    "rhms_rhm":  {"func": tests.rhms_rhm,  "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l2", "hm2", "ub2", "col"], "argl1": 0},
    "rhms_rhms": {"func": tests.rhms_rhms, "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["ub2", "col"], "argl1": 0, "argl2": 0}, 
    "rhms_rhmv": {"func": tests.rhms_rhms, "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l2", "ub2", "col"], "argl1": 0},
    "rhms_rhmc": {"func": tests.rhms_rhmc, "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["ub2", "col"], "argl1": 0},
    "rhms_whm":  {"func": tests.rhms_whm,  "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l2", "hm2", "ub2", "col"], "argl1": 0},
    "rhms_rw":   {"func": tests.rhms_rw,   "setup_rw_cts": [0, 1, 2, 3   ], "vars": ["col"], "argl1": 0},
    "rhms_mmc":  {"func": tests.rhms_mmc,  "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l2", "ub2", "col"], "argl1": 0},
    "rhms_mmcs": {"func": tests.rhms_mmc,  "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l2", "ub2", "col"], "flag2": "S", "argl1": 0},
    "rhms_act":  {"func": tests.rhms_act,  "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l2", "ub2", "col"], "argl1": 0},
    "rhms_hlt":  {"func": tests.rhms_hlt,  "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["col"], "argl1": 0},

    "rhmv_rhm":  {"func": tests.rhms_rhm,  "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l1", "l2", "hm2", "ub2", "col"]},
    "rhmv_rhms": {"func": tests.rhms_rhms, "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l1", "ub2", "col"], "argl2": 0}, 
    "rhmv_rhmv": {"func": tests.rhms_rhms, "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l1", "l2", "ub2", "col"]},
    "rhmv_rhmc": {"func": tests.rhms_rhmc, "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l1", "ub2", "col"]},
    "rhmv_whm":  {"func": tests.rhms_whm,  "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l1", "l2", "hm2", "ub2", "col"]},
    "rhmv_rw":   {"func": tests.rhms_rw,   "setup_rw_cts": [0, 1, 2, 3   ], "vars": ["l1", "col"]},
    "rhmv_mmc":  {"func": tests.rhms_mmc,  "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l1", "l2", "ub2", "col"]},
    "rhmv_mmcs": {"func": tests.rhms_mmc,  "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l1", "l2", "ub2", "col"], "flag2": "S"},
    "rhmv_act":  {"func": tests.rhms_act,  "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l1", "l2", "ub2", "col"]},
    "rhmv_hlt":  {"func": tests.rhms_hlt,  "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l1", "col"]},

    "rhmc_rhm":  {"func": tests.rhmc_rhm,  "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l2", "ub2"]},
    "rhmc_rhms": {"func": tests.rhmc_rhms, "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["ub2", "col"], "argl2": 0}, 
    "rhmc_rhmv": {"func": tests.rhmc_rhms, "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l2", "ub2", "col"]},
    "rhmc_rhmc": {"func": tests.rhmc_rhmc, "setup_rw_cts": [0, 1, 2, 3, 4], "vars": []},
    "rhmc_whm":  {"func": tests.rhmc_whm,  "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l2", "ub2"]},
    "rhmc_rw":   {"func": tests.rhmc_rw,   "setup_rw_cts": [0, 1, 2, 3   ], "vars": []},
    "rhmc_mmc":  {"func": tests.rhmc_mmc,  "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l2", "ub2"]},
    "rhmc_mmcs": {"func": tests.rhmc_mmc,  "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l2", "ub2"], "flag2": "S"},
    "rhmc_act":  {"func": tests.rhmc_act,  "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l2", "ub2"]},
    "rhmc_hlt":  {"func": tests.rhmc_hlt,  "setup_rw_cts": [0, 1, 2, 3, 4], "vars": []},

    "whm_rhm":   {"func": tests.whm_rhm,   "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l1", "l2", "hm2", "ub2"]},
    "whm_rhms":  {"func": tests.whm_rhms,  "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l1", "hm2", "ub2", "col"], "argl2": 0},
    "whm_rhmv":  {"func": tests.whm_rhms,  "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l1", "l2", "hm2", "ub2", "col"]},
    "whm_rhmc":  {"func": tests.whm_rhmc,  "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l1", "ub2"]},
    "whm_whm":   {"func": tests.whm_whm,   "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l1", "l2", "hm2", "ub2"]},
    "whm_rw":    {"func": tests.whm_rw,    "setup_rw_cts": [0, 1, 2, 3   ], "vars": ["l1"]},
    "whm_mmc":   {"func": tests.whm_mmc,   "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l1", "l2", "ub2"]},
    "whm_mmcs":  {"func": tests.whm_mmc,   "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l1", "l2", "ub2"], "flag2": "S"},
    "whm_act":   {"func": tests.whm_act,   "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l1", "l2", "ub2"]},
    "whm_hlt":   {"func": tests.whm_hlt,   "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l1"]},

    "rw_rhm":    {"func": tests.rw_rhm,    "setup_rw_cts": [0, 1, 2, 3   ], "vars": ["l2"]},
    "rw_rhms":   {"func": tests.rw_rhms,   "setup_rw_cts": [0, 1, 2, 3   ], "vars": ["col"], "argl2": 0}, # TODO: any params for this guy?
    "rw_rhmv":   {"func": tests.rw_rhms,   "setup_rw_cts": [0, 1, 2, 3   ], "vars": ["l2", "col"]},
    "rw_rhmc":   {"func": tests.rw_rhmc,   "setup_rw_cts": [0, 1, 2, 3   ], "vars": []},
    "rw_whm":    {"func": tests.rw_whm,    "setup_rw_cts": [0, 1, 2, 3   ], "vars": ["l2"]},
    "rw_rw":     {"func": tests.rw_rw,     "setup_rw_cts": [0, 1, 2      ], "vars": []},
    "rw_mmc":    {"func": tests.rw_mmc,    "setup_rw_cts": [0, 1, 2, 3   ], "vars": ["l2"]},
    "rw_mmcs":   {"func": tests.rw_mmc,    "setup_rw_cts": [0, 1, 2, 3   ], "vars": ["l2"], "flag2": "S"},
    "rw_act":    {"func": tests.rw_act,    "setup_rw_cts": [0, 1, 2, 3   ], "vars": ["l2"]},
    "rw_hlt":    {"func": tests.rw_hlt,    "setup_rw_cts": [0, 1, 2, 3   ], "vars": []},

    "mmc_rhm":   {"func": tests.mmc_rhm,   "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l1", "l2", "ub2"]},
    "mmc_rhms":  {"func": tests.mmc_rhms,  "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l1", "ub2", "col"], "argl2": 0},
    "mmc_rhmv":  {"func": tests.mmc_rhms,  "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l1", "l2", "ub2", "col"]},
    "mmc_rhmc":  {"func": tests.mmc_rhmc,  "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l1", "ub2"]},
    "mmc_whm":   {"func": tests.mmc_whm,   "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l1", "l2", "ub2"]},
    "mmc_rw":    {"func": tests.mmc_rw,    "setup_rw_cts": [   1, 2, 3   ], "vars": ["l1"]},
    "mmc_mmc":   {"func": tests.mmc_mmc,   "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l1", "l2", "ub2", "acc2"]},
    "mmc_mmcs":  {"func": tests.mmc_mmc,   "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l1", "l2", "ub2", "acc2"], "flag2": "S"},
    "mmc_act":   {"func": tests.mmc_act,   "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l1", "l2", "ub2", "acc2"]},
    "mmc_hlt":   {"func": tests.mmc_hlt,   "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l1"]},

    "mmcs_rhm":  {"func": tests.mmc_rhm,   "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l1", "l2", "ub2"], "flag1": "S"},
    "mmcs_rhms": {"func": tests.mmc_rhms,  "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l1", "ub2", "col"], "flag1": "S", "argl2": 0},
    "mmcs_rhmv": {"func": tests.mmc_rhms,  "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l1", "l2", "ub2", "col"], "flag1": "S"},
    "mmcs_rhmc": {"func": tests.mmc_rhmc,  "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l1", "ub2"], "flag1": "S"},
    "mmcs_whm":  {"func": tests.mmc_whm,   "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l1", "l2", "ub2"], "flag1": "S"},
    "mmcs_rw":   {"func": tests.mmc_rw,    "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l1"], "flag1": "S"},
    "mmcs_mmc":  {"func": tests.mmc_mmc,   "setup_rw_cts": [      2, 3, 4], "vars": ["l1", "l2", "ub2", "acc2"], "flag1": "S"},
    "mmcs_mmcs": {"func": tests.mmc_mmc,   "setup_rw_cts": [      2, 3, 4], "vars": ["l1", "l2", "ub2", "acc2"], "flag1": "S", "flag2": "S"},
    "mmcs_act":  {"func": tests.mmc_act,   "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l1", "l2", "ub2", "acc2"], "flag1": "S"},
    "mmcs_hlt":  {"func": tests.mmc_hlt,   "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l1"], "flag1": "S"},

    "act_rhm":   {"func": tests.act_rhm,   "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l1", "l2", "ub2"]},
    "act_rhms":  {"func": tests.act_rhms,  "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l1", "ub2", "col"], "argl2": 0},
    "act_rhmv":  {"func": tests.act_rhms,  "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l1", "l2", "ub2", "col"]},
    "act_rhmc":  {"func": tests.act_rhmc,  "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l1", "ub2"]},
    "act_whm":   {"func": tests.act_whm,   "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l1", "l2", "ub2"]},
    "act_rw":    {"func": tests.act_rw,    "setup_rw_cts": [0, 1, 2, 3   ], "vars": ["l1"]},
    "act_mmc":   {"func": tests.act_mmc,   "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l1", "l2", "ub2", "acc2"]},
    "act_mmcs":  {"func": tests.act_mmc,   "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l1", "l2", "ub2", "acc2"], "flag2": "S"},
    "act_act":   {"func": tests.act_act,   "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l1", "l2", "ub2", "acc2"]},
    "act_hlt":   {"func": tests.act_hlt,   "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l1"]},
}

# if the parametrized test under consideration uses a parameter for instr2's 
# starting address in a given memory (HM, UB, or ACC), calculate all possible
# values of that parameter and return them in a list.
# if the parametrized test doesn't use the parameter, return [-1].
def get_i2_addrs(has_addr, l1, l2):
    if not has_addr:
        return [-1]

    # return [0, l2] # scheme for "diff" and "same" to compare against baseline

    addrs = set() # use set to remove duplicates
    for l1_adjust in [0, l1//2, l1]: # 1-X, 2-X, 3-X
        for l2_adjust in [0, l2//2, l2]: # X-1, X-2, X-3
            addrs.add(l2 + l1_adjust - l2_adjust)

    addrs.add(1) # minf
    addrs.add(l2 + min(l1-l2, 0) - 1) # maxf
    addrs.add(l2 + max(l1-l2, 0) + 1) # maxb
    addrs.add(l2 + l1 - 1) # minb

    addrs_list = sorted(list(addrs))
    
    # remove all addrs that place instr2 strictly higher than instr1
    # (instr2 start = addr[i] > instr1 end = l2 + l1 - 1)
    while addrs_list[-1] >= l1 + l2:
        addrs_list.pop()
    return addrs_list

# if the parametrized test under consideration uses a parameter for instr1's or
# instr2's lengths, calculate all possible lengths and return them in a list. 
# if the parametrized test doesn't use the parameter, return [1]. this allows 
# for RHM.S and WHM.S to have an instruction length of 1 even when they aren't
# parametrized on length
def get_lengths(has_len, matsize):
    if not has_len:
        return [1]
    # return [int(0.5*matsize), int(matsize)]
    return [int(0.5*matsize), int(matsize), int(2*matsize)]

# if the parametrized test under consideration is parametrized by column 
# position (RHM.S or WHM.S), calculate the desired vector column address values
def get_cols(has_col, matsize):
    if not has_col:
        return [-1]
    return [0, matsize-1]
        
# nested dictionary insertion. e.g. if keys = ["a", "b", "c"], d["a"]["b"]["c"]
# will be set to `value`. intermediate steps in the dictionary will be added
# along the way if needed (e.g. if d = {} before the function call)
def set_nested_dict(d: dict, keys, value):
    for key in keys[:-1]:
        d = d.setdefault(key, {})
    d[keys[-1]] = value

# return true if d[path[0]][path[1]]...[path[-1]] is defined, false otherwise
def dict_contains_path(d: dict, path):
    for item in path:
        if type(d) is not dict or d.get(item) is None:
            return False
        d = d[item]
    return True

# deep comparison between two dictionaries (or integers)
def dict_deep_compare(value1, value2):
    if type(value1) is not type(value2): 
        return False

    if type(value1) is int or type(value1) is bool:
        return value1 == value2

    for key in value1.keys() | value2.keys():
        if key not in value1:
            return False
        if key not in value2:
            return False

        if not dict_deep_compare(value1[key], value2[key]):
            return False

    return True

# deep comparison between the common values of two dictionaries (or integers)
def dict_common_compare(value1, value2, path):
    
    if type(value1) is not type(value2): 
        print(path, ": ", value1, "!=", value2)
        return False

    if type(value1) is int:
        if value1 != value2:
            print(path, ": ", value1, "!=", value2)
        return value1 == value2

    verdict = True
    for key in value1.keys() & value2.keys():
        path.append(key)
        if not dict_common_compare(value1[key], value2[key], path):
            # print(path, ": ", value1[key], "!=", value2[key])
            verdict = False
        path.pop()

    return verdict

# recursively simplify the dictionary when all values are the same
# e.g. d_in  = {a: {a1: 1, a2: 2, a3: 3}, b: {b1: 0, b2: 0, b3: 0}} becomes
#      d_out = {a: {a1: 1, a2: 2, a3: 3}, b: 0}
# return a new dict
def simplify_dict(d: dict):
    # this is a bottom-up algorithm, so simplify all the sub-dicts first and
    # store in a new dict
    d_simp = {}
    for key in d.keys():
        if type(d[key]) is dict:
            d_simp[key] = simplify_dict(d[key])
        else:
            d_simp[key] = d[key]
    # then check if the value of every key-value pair is 
    # 1. an integer 2. the same integer
    # if so, then you can simplify the whole dict down to the common value. if
    # not, you can't simplify, so just return the dict
    else:
        value = None
        for key in d_simp.keys():
            if value is not None and not dict_deep_compare(value, d_simp[key]):
                return d_simp
            value = d_simp[key]
        return value

if __name__ == "__main__":
    commands = []
    categories = ["rhm", "rhms", "rhmv", "rhmc", "whm", "rw", "mmc", "mmcs", 
                  "act", "hlt"]
    bitwidths = [32]
    matsizes = [4, 8, 16] #, 32]
    base_distance = 150
    if len(sys.argv) < 2:
        print("No test name entered in command line. Enter a test name: ")
        test_folder = input()
    else:
        test_folder = sys.argv[1]

    if Path(f"{test_folder}/results.json").exists():
        with open(f"{test_folder}/results.json") as result_file:
            d = json.load(result_file)
    else:
        d = {}

    # generate all squishtest commands:

    # iterate over all valid combinations of instr1_instr2 pairs
    for instr1 in categories[:-1]: # hlt cannot be instr1
        for instr2 in categories:
            # grab the valid parameters for the instr1_instr2 pair
            instr_pair = instr1 + "_" + instr2
            has_l1 = "l1" in info_map[instr_pair]["vars"]
            has_l2 = "l2" in info_map[instr_pair]["vars"]
            has_hm2 = "hm2" in info_map[instr_pair]["vars"]
            has_ub2 = "ub2" in info_map[instr_pair]["vars"]
            has_acc2 = "acc2" in info_map[instr_pair]["vars"]
            has_flag1 = "flag1" in info_map[instr_pair]
            has_flag2 = "flag2" in info_map[instr_pair]
            has_col = "col" in info_map[instr_pair]["vars"]
            setup_rw_cts = info_map[instr_pair]["setup_rw_cts"]
            func = info_map[instr_pair]["func"]
            # set arg length if it has a value, otherwise set to -1. arg length
            # is used for variants of RHM.S and WHM.S instructions, which have
            # an effective length of 1 but the length argument has to be 0
            if "argl1" in info_map[instr_pair]:
                argl1 = info_map[instr_pair]["argl1"]
            else:
                argl1 = -1
            if "argl2" in info_map[instr_pair]:
                argl2 = info_map[instr_pair]["argl2"]
            else:
                argl2 = -1
            
            # iterate over all bitwidth and matsizes
            for b in bitwidths:
                for m in matsizes:
                    # calculate the lengths to test for each instr (if 
                    # applicable)
                    l1s = get_lengths(has_l1, m)
                    l2s = get_lengths(has_l2, m)
                    cols = get_cols(has_col, m)

                    # iterate over the number of weights in the fifo queue at 
                    # the time of instr1, and the possible instr lengths
                    for setup_rw_ct in setup_rw_cts: 
                        for l1 in l1s:
                            for l2 in l2s:
                                # calculate the starting HM, UB, and ACC 
                                # addresses for instr2's, assuming that instr1
                                # starts at address `l2`
                                hm2s = get_i2_addrs(has_hm2, l1, l2)
                                ub2s = get_i2_addrs(has_ub2, l1, l2)
                                acc2s = get_i2_addrs(has_acc2, l1, l2)

                                # iterate over instr2's starting HM, UB, and ACC
                                # addresses
                                for hm2 in hm2s:
                                    for ub2 in ub2s:
                                        for acc2 in acc2s:
                                            for col in cols:
                                                # single squishtest instance: 
                                                # create a ParamHandler to store
                                                # and manage the parameters
                                                ph = ParamHandler(func, 
                                                    instr1, instr2, b, m, 
                                                    not HAZARD_DETECTION, 
                                                    setup_rw_ct, base_distance, 
                                                    test_folder, UB_ADDR_SIZE
                                                )
                                                ph.set_l1(l1)
                                                ph.set_l2(l2)
                                                
                                                if argl1 == -1:
                                                    ph.set_argl1(l1)
                                                else:
                                                    ph.set_argl1(argl1)
                                                if argl2 == -1:
                                                    ph.set_argl2(l2)
                                                else:
                                                    ph.set_argl2(argl2)
                                                
                                                if has_hm2:
                                                    ph.set_hm2(hm2)
                                                if has_ub2:
                                                    ph.set_ub2(ub2)
                                                if has_acc2: 
                                                    ph.set_acc2(acc2)
                                                if has_flag1:
                                                    ph.set_flags1(info_map[instr_pair]["flag1"])
                                                if has_flag2:
                                                    ph.set_flags2(info_map[instr_pair]["flag2"])
                                                if has_col:
                                                    ph.set_col(col)

                                                # add the ParamHandler instance 
                                                # to the commands list, along 
                                                # with the path to place the 
                                                # results of this test in the 
                                                # global result dict
                                                dict_path_list = ph.get_dict_path_list()
                                                if not dict_contains_path(d, dict_path_list):
                                                    commands.append((
                                                        ph.get_driver_func(),
                                                        dict_path_list
                                                    ))

    # run the commands

    # set up the result dictionary with all the possible paths to store 
    # beforehand so that the dictionary is always sorted
    for (_, dict_path) in commands:
        set_nested_dict(d, dict_path, None)

    print(f"Running squishtests for {len(commands)} commands:")
    counter = 0
    start_time = time.time()

    # run each command as a separate process with a configurable number of cores
    with ProcessPoolExecutor(max_workers=154) as executor:
        future_to_input = {executor.submit(ph_driver): dict_path 
                           for (ph_driver, dict_path) in commands}
        
        for future in as_completed(future_to_input):
            # as each command completes, add it's result to the global result
            # dictionary
            dict_path = future_to_input[future]
            result = future.result()
            set_nested_dict(d, dict_path, result)

            # regular progress update with expected completion time
            # TODO: smarter ETA system that takes the computed matrix sizes into
            # account
            counter += 1
            if counter % 25 == 0:
                current_time = time.time()
                elapsed_time = current_time - start_time
                eta = elapsed_time / counter * (len(commands) - counter)
                print(f"Completed {counter} out of {len(commands)} commands.", file=sys.stderr)
                print(f"Time elapsed: {current_time - start_time}s", file=sys.stderr)
                print(f"Completion ETA: {eta}s\n", file=sys.stderr)

    # final timing
    end_time = time.time()
    print(f"Finished {len(commands)} tests in {end_time - start_time}s.")

    # create an abridged results dict
    simp_d = {}
    for key in d.keys():
        simp_d[key] = simplify_dict(d[key])
    
    # store results

    # global
    with open(f"{test_folder}/results.json", "w") as reg_f:
        json.dump(d, reg_f, indent=2)
    with open(f"{test_folder}/results_abridged.json", "w") as simp_f:
        json.dump(simp_d, simp_f, indent=2)
    
    # results for each instr combo
    for instr1 in categories[:-1]: # hlt cannot be instr1
        for instr2 in categories:
            instrs = f"{instr1}_{instr2}"
            with open(f"{test_folder}/{instrs}/results.json", "w") as reg_f:
                json.dump(d[instrs], reg_f, indent=2)
            with open(f"{test_folder}/{instrs}/results_abridged.json", "w") as simp_f:
                json.dump(simp_d[instrs], simp_f, indent=2)
