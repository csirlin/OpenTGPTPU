# run all squishtests

import os
import tests
from test_utils import ParamHandler
import sys
import json
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

# add base folder (OPENTGPTPU) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from config import HAZARD_DETECTION

# maps an (instr1_instr2) pair to:
#   the parametrized squishtest to call 
#   the valid setup RW counts
#   the parametrized vars (possible vars are l1, l2, hm2, ub2, and acc2)
#   flags on instr1 and instr2 (currently just used for MMC.S)
info_map = {
    "rhm_rhm":   {"func": tests.rhm_rhm,   "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l1", "l2", "hm2", "ub2"]},
    "rhm_whm":   {"func": tests.rhm_whm,   "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l1", "l2", "hm2", "ub2"]},
    "rhm_rw":    {"func": tests.rhm_rw,    "setup_rw_cts": [0, 1, 2, 3   ], "vars": ["l1"]},
    "rhm_mmc":   {"func": tests.rhm_mmc,   "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l1", "l2", "ub2"]},
    "rhm_mmcs":  {"func": tests.rhm_mmc,   "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l1", "l2", "ub2"], "flag2": "S"},
    "rhm_act":   {"func": tests.rhm_act,   "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l1", "l2", "ub2"]},
    "rhm_hlt":   {"func": tests.rhm_hlt,   "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l1"]},

    "whm_rhm":   {"func": tests.whm_rhm,   "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l1", "l2", "hm2", "ub2"]},
    "whm_whm":   {"func": tests.whm_whm,   "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l1", "l2", "hm2", "ub2"]},
    "whm_rw":    {"func": tests.whm_rw,    "setup_rw_cts": [0, 1, 2, 3   ], "vars": ["l1"]},
    "whm_mmc":   {"func": tests.whm_mmc,   "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l1", "l2", "ub2"]},
    "whm_mmcs":  {"func": tests.whm_mmc,   "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l1", "l2", "ub2"], "flag2": "S"},
    "whm_act":   {"func": tests.whm_act,   "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l1", "l2", "ub2"]},
    "whm_hlt":   {"func": tests.whm_hlt,   "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l1"]},

    "rw_rhm":    {"func": tests.rw_rhm,    "setup_rw_cts": [0, 1, 2, 3   ], "vars": ["l2"]},
    "rw_whm":    {"func": tests.rw_whm,    "setup_rw_cts": [0, 1, 2, 3   ], "vars": ["l2"]},
    "rw_rw":     {"func": tests.rw_rw,     "setup_rw_cts": [0, 1, 2      ], "vars": []},
    "rw_mmc":    {"func": tests.rw_mmc,    "setup_rw_cts": [0, 1, 2, 3   ], "vars": ["l2"]},
    "rw_mmcs":   {"func": tests.rw_mmc,    "setup_rw_cts": [0, 1, 2, 3   ], "vars": ["l2"], "flag2": "S"},
    "rw_act":    {"func": tests.rw_act,    "setup_rw_cts": [0, 1, 2, 3   ], "vars": ["l2"]},
    "rw_hlt":    {"func": tests.rw_hlt,    "setup_rw_cts": [0, 1, 2, 3   ], "vars": []},

    "mmc_rhm":   {"func": tests.mmc_rhm,   "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l1", "l2", "ub2"]},
    "mmc_whm":   {"func": tests.mmc_whm,   "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l1", "l2", "ub2"]},
    "mmc_rw":    {"func": tests.mmc_rw,    "setup_rw_cts": [   1, 2, 3   ], "vars": ["l1"]},
    "mmc_mmc":   {"func": tests.mmc_mmc,   "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l1", "l2", "ub2", "acc2"]},
    "mmc_mmcs":  {"func": tests.mmc_mmc,   "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l1", "l2", "ub2", "acc2"], "flag2": "S"},
    "mmc_act":   {"func": tests.mmc_act,   "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l1", "l2", "ub2", "acc2"]},
    "mmc_hlt":   {"func": tests.mmc_hlt,   "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l1"]},

    "mmcs_rhm":  {"func": tests.mmc_rhm,   "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l1", "l2", "ub2"], "flag1": "S"},
    "mmcs_whm":  {"func": tests.mmc_whm,   "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l1", "l2", "ub2"], "flag1": "S"},
    "mmcs_rw":   {"func": tests.mmc_rw,    "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l1"], "flag1": "S"},
    "mmcs_mmc":  {"func": tests.mmc_mmc,   "setup_rw_cts": [      2, 3, 4], "vars": ["l1", "l2", "ub2", "acc2"], "flag1": "S"},
    "mmcs_mmcs": {"func": tests.mmc_mmc,   "setup_rw_cts": [      2, 3, 4], "vars": ["l1", "l2", "ub2", "acc2"], "flag1": "S", "flag2": "S"},
    "mmcs_act":  {"func": tests.mmc_act,   "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l1", "l2", "ub2", "acc2"], "flag1": "S"},
    "mmcs_hlt":  {"func": tests.mmc_hlt,   "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l1"], "flag1": "S"},

    "act_rhm":   {"func": tests.act_rhm,   "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l1", "l2", "ub2"]},
    "act_whm":   {"func": tests.act_whm,   "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l1", "l2", "ub2"]},
    "act_rw":    {"func": tests.act_rw,    "setup_rw_cts": [0, 1, 2, 3   ], "vars": ["l1"]},
    "act_mmc":   {"func": tests.act_mmc,   "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l1", "l2", "ub2", "acc2"]},
    "act_mmcs":  {"func": tests.act_mmc,   "setup_rw_cts": [   1, 2, 3, 4], "vars": ["l1", "l2", "ub2", "acc2"], "flag2": "S"},
    "act_act":   {"func": tests.act_act,   "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l1", "l2", "ub2", "acc2"]},
    "act_hlt":   {"func": tests.act_hlt,   "setup_rw_cts": [0, 1, 2, 3, 4], "vars": ["l1"]},
}

# TODO: use params object as a passthrough into squishtest?

# if the parametrized test under consideration uses a parameter for instr2's 
# starting address in a given memory (HM, UB, or ACC), calculate all possible
# values of that parameter and return them in a list.
# if the parametrized test doesn't use the parameter, return [-1].
def get_i2_addrs(has_addr, l1, l2):
    if not has_addr:
        return [-1]

    return [0, l2] # scheme for "diff" and "same" to compare against baseline

    # eventual scheme
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
# if the parametrized test doesn't use the parameter, return [-1].
def get_lengths(has_len, matsize):
    if not has_len:
        return [-1]
    return [int(0.5*matsize), int(matsize)]
    # return [int(0.5*matsize), int(matsize), int(2*matsize)]

# nested dictionary insertion. e.g. if keys = ["a", "b", "c"], d["a"]["b"]["c"]
# will be set to `value`. intermediate steps in the dictionary will be added
# along the way if needed (e.g. if d = {} before the function call)
def set_nested_dict(d: dict, keys, value):
    for key in keys[:-1]:
        d = d.setdefault(key, {})
    d[keys[-1]] = value
    

if __name__ == "__main__":
    d = {}
    commands = []
    categories = ["rhm", "whm", "rw", "mmc", "mmcs", "act", "hlt"]
    bitwidths = [32]
    matsizes = [4] # [4, 8, 16, 32]
    base_distance = 150
    print("Enter a test name: ")
    test_folder = input()

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
            setup_rw_cts = info_map[instr_pair]["setup_rw_cts"]
            func = info_map[instr_pair]["func"]

            # iterate over all bitwidth and matsizes
            for b in bitwidths:
                for m in matsizes:
                    # calculate the lengths to test for each instr (if 
                    # applicable)
                    l1s = get_lengths(has_l1, m)
                    l2s = get_lengths(has_l2, m)

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
                                            # single squishtest instance: 
                                            # create a ParamHandler to store and
                                            # manage the parameters
                                            ph = ParamHandler(func, 
                                                instr1, instr2, b, m, 
                                                not HAZARD_DETECTION, 
                                                setup_rw_ct, base_distance, 
                                                test_folder
                                            )
                                            if has_l1:
                                                ph.set_l1(l1)
                                            if has_l2:
                                                ph.set_l2(l2)
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

                                            # add the ParamHandler instance to 
                                            # the commands list, along with the 
                                            # path to place the results of this
                                            # test in the global result dict
                                            commands.append((
                                                ph.get_driver_func(),
                                                ph.get_dict_path_list()
                                            ))

    # run the commands

    counter = 0
    start_time = time.time()
    # print("here", file=sys.stderr)

    # for (ph_driver, dict_path) in commands:
    #     counter += 1
    #     result = ph_driver()
    #     set_nested_dict(d, dict_path, result)

    #     if counter%25 == 0:
    #         current_time = time.time()
    #         elapsed_time = current_time - start_time
    #         eta = elapsed_time / counter * (len(commands) - counter)
    #         print(f"Completed {counter} out of {len(commands)} commands.", file=sys.stderr)
    #         print(f"Time elapsed: {current_time - start_time}s", file=sys.stderr)
    #         print(f"Completion ETA: {eta}s", file=sys.stderr)

    # exit(0)

    # run each command as a separate process with a configurable number of cores
    with ProcessPoolExecutor(max_workers=3) as executor:
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
                print(f"Completion ETA: {eta}s", file=sys.stderr)

    # store results and final timing
    with open(f"{test_folder}/results.json", "w") as result_file:
        json.dump(d, result_file, indent=2)

    end_time = time.time()
    print(f"Finished {len(commands)} tests in {end_time - start_time}s.")
