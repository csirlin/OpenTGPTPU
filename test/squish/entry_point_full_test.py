# run a set of squishtests.
# call from working directory test/squish like
# python entry_point_full_test.py {instr1}_{instr2} {L1} {L2} {test_folder}
# or let this file be called by entry_point_full_test_caller.py to run the full
# squishtest suite.

import os
import test_utils
import sys
import json

function_map = {
    "rhm_rhm": test_utils.test_all_rhm_rhm,
    "rhm_whm": test_utils.test_all_rhm_whm,
    "rhm_rw": test_utils.test_all_rhm_rw,
    "rhm_mmc": test_utils.test_all_rhm_mmc,
    "rhm_act": test_utils.test_all_rhm_act,
    "rhm_hlt": test_utils.test_all_rhm_hlt,
    "whm_rhm": test_utils.test_all_whm_rhm,
    "whm_whm": test_utils.test_all_whm_whm,
    "whm_rw": test_utils.test_all_whm_rw,
    "whm_mmc": test_utils.test_all_whm_mmc,
    "whm_act": test_utils.test_all_whm_act,
    "whm_hlt": test_utils.test_all_whm_hlt,
    "rw_rhm": test_utils.test_all_rw_rhm,
    "rw_whm": test_utils.test_all_rw_whm,
    "rw_rw": test_utils.test_all_rw_rw,
    "rw_mmc": test_utils.test_all_rw_mmc,
    "rw_act": test_utils.test_all_rw_act,
    "rw_hlt": test_utils.test_all_rw_hlt,
    "mmc_rhm": test_utils.test_all_mmc_rhm,
    "mmc_whm": test_utils.test_all_mmc_whm,
    "mmc_rw": test_utils.test_all_mmc_rw,
    "mmc_mmc": test_utils.test_all_mmc_mmc,
    "mmc_act": test_utils.test_all_mmc_act,
    "mmc_hlt": test_utils.test_all_mmc_hlt,
    "act_rhm": test_utils.test_all_act_rhm,
    "act_whm": test_utils.test_all_act_whm,
    "act_rw": test_utils.test_all_act_rw,
    "act_mmc": test_utils.test_all_act_mmc,
    "act_act": test_utils.test_all_act_act,
    "act_hlt": test_utils.test_all_act_hlt,
}

# set test parameters
test_utils.START_DISTANCE = 110
chosen_test = sys.argv[1]
test_utils.L1 = float(sys.argv[2])
test_utils.L2 = float(sys.argv[3])
test_utils.TEST_FOLDER = sys.argv[4]

os.makedirs(test_utils.TEST_FOLDER, exist_ok=True)

# run the tests (select either reg or nop)
result = function_map[chosen_test](test_function=test_utils.min_viable_distance_all, bitwidths=[32], matsizes=[4, 8, 16, 32]) # distance test with nops
# result = function_map[chosen_test](test_function=test_utils.no_nop_comparison_all, bitwidths=[32], matsizes=[4, 8, 16, 32]) # hazard detecting, no nops

# write to json and print to stdout
json.dump(result, open(f"{test_utils.TEST_FOLDER}/{chosen_test}.json", "w"), indent=2)
print(result)
