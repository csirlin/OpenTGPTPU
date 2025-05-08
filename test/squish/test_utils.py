# utilities for running squish tests
from squishtest import squish_test
TEST_FOLDER = "test"
START_DISTANCE = 50
L1 = 1
L2 = 1


# run a squish test with chosen bitwidth and matsize for different distances. 
# binary search the distances in the range [1, START_DISTANCE) to find the 
# minimum distance that works. 
# return the lowest distance that was successful. If the final distance is 
# reported as START_DISTANCE, it means that the test failed at all distances in 
# the range. It could work at a distance d >= START_DISTANCE, or it could always
# fail. Either way, it's a signal to investigate further and/or rerun with a 
# higher START_DISTANCE.
def min_viable_distance_fixed(function, bitwidth, matsize):
    left = 1
    right = START_DISTANCE
    while right - left > 0:
        mid = (left + right)//2
        result = function(mid, bitwidth, matsize, True)
        if result:
            right = mid
        else:
            left = mid+1
    return right
    
# find the mimimum viable distance for a variety of bitwidths and matsizes.
# return a nested dictionary that holds the minimum viable distance for each
# combination of bitwidth and matsize. accessed as dist = d[bitwidth][matsize].
def min_viable_distance_all(function, bitwidths, matsizes):
    d = {}
    for bitwidth in bitwidths:
        b_index = "b" + str(bitwidth)
        d[b_index] = {}
        for matsize in matsizes:
            distance = min_viable_distance_fixed(function, bitwidth, matsize)
            m_index = "m" + str(matsize)
            d[b_index][m_index] = distance
    return d

# compare the control test with the no-NOP version for all bitwidths and 
# matsizes. return a nested dictionary that holds the result for each 
# combination of bitwidth and matsize. accessed as 
# result = d[bitwidth][matsize].
def no_nop_comparison_all(squishtest, bitwidths, matsizes):
    d = {}
    for bitwidth in bitwidths:
        b_index = "b" + str(bitwidth)
        d[b_index] = {}
        for matsize in matsizes:
            result = squishtest(START_DISTANCE, bitwidth, matsize, False)
            m_index = "m" + str(matsize)
            d[b_index][m_index] = result
    return d

### custom tests ###

# test the behavior of the MMC switch instruction. the expected behavior is that
# a loaded weight will enter the back of the queue. An MMC with or without the
# .S flag will use the weight at the front of the queue. If the .S flag is not
# used, then the instruction will use the front weight and not switch it. If the
# .S is used, then the instruction will use the front weight and afterwards, 
# discard the front instruction to let the next one come to the front.
# this test loads HM0, HM1, and HM2 to UB0, UB1, and UB2, respectively.
# it then loads RW0 and RW1 to the weight queue.
# it then does the following multiplication operations:
#     UB0 * RW0 -> ACC0 (no .S)
#     UB1 * RW0 -> ACC1 (.S)
#     UB2 * RW1 -> ACC2 (.S but it doesn't matter)
# it then writes ACC0 to UB3, ACC1 to UB4, and ACC2 to UB5.
# it then writes UB3 to HM3, UB4 to HM4, and UB5 to HM5.
# the expected results are that HM3 = HM0 * RW0, HM4 = HM1 * RW0, and 
# HM5 = HM2 * RW1.
def test_mmc_switch_behavior(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1", "RHM 1 1 1", "RHM 2 2 1",
                              "RW 0", "RW 1",
                              "MMC 0 0 1", "MMC.S 1 1 1", "MMC.S 2 2 1",
                              "ACT 0 3 1", "ACT 1 4 1", "ACT 2 5 1",
                              "WHM 3 3 1", "WHM 4 4 1", "WHM 5 5 1"],
                       instrs=["NOP", "NOP"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="test_mmc_switch_behavior",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance=START_DISTANCE, use_nops=use_nops)


### RHM-RHM TESTS ###
def test_all_rhm_rhm(test_function, bitwidths, matsizes):
    return {
        "rhm_rhm_diff_hm_diff_ub": test_function(rhm_rhm_diff_hm_diff_ub, bitwidths, matsizes),
        "rhm_rhm_diff_hm_same_ub": test_function(rhm_rhm_diff_hm_same_ub, bitwidths, matsizes),
        "rhm_rhm_same_hm_diff_ub": test_function(rhm_rhm_same_hm_diff_ub, bitwidths, matsizes),
        "rhm_rhm_same_hm_same_ub": test_function(rhm_rhm_same_hm_same_ub, bitwidths, matsizes)
    }

# from HM0 to UB0 and from HM1 to UB1 (no overlap in HM or UB)
# setup reads the wrong matrices to slots 0 and 1 to start with. that way, the
#     test confirms that RHM overwrites existing data correctly.
# instrs write the correct matrices to slots 0 and 1.
def rhm_rhm_diff_hm_diff_ub(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 2 0 1", "RHM 3 1 1"],
                       instrs=[f"RHM 0 0 {L1}", f"RHM 1 1 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rhm_rhm_diff_hm_diff_ub", 
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# from HM0 to UB0 and from HM1 to UB0 (same destination in UB)
# setup is not needed to test that data is overwritten correctly.
# instrs write HM 0 to UB 0 and then overwrite UB 0 with HM 1.
def rhm_rhm_diff_hm_same_ub(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=[],
                       instrs=[f"RHM 0 0 {L1}", f"RHM 1 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rhm_rhm_diff_hm_same_ub", 
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# from HM0 to UB0 and from HM0 to UB1 (same origin in HM)
# setup is not needed to test that data is written to two different places
#     correctly.
# instrs write HM 0 to UB 0 and write HM 0 again to UB 1.
def rhm_rhm_same_hm_diff_ub(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=[],
                       instrs=[f"RHM 0 0 {L1}", f"RHM 0 1 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rhm_rhm_same_hm_diff_ub", 
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# from HM0 to UB0 and from HM0 to UB0 (same origin in HM and destination in UB)
# setup is not needed to test that data is written to the same place twice.
# instrs write HM 0 to UB 0 and then write HM 0 to UB 0 again.
def rhm_rhm_same_hm_same_ub(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=[],
                       instrs=[f"RHM 0 0 {L1}", f"RHM 0 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rhm_rhm_same_hm_same_ub", 
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)



### RHM-WHM TESTS ###
def test_all_rhm_whm(test_function, bitwidths, matsizes):
    return {
        "rhm_whm_diff_hm_diff_ub": test_function(rhm_whm_diff_hm_diff_ub, bitwidths, matsizes),
        "rhm_whm_diff_hm_same_ub": test_function(rhm_whm_diff_hm_same_ub, bitwidths, matsizes),
        "rhm_whm_same_hm_diff_ub": test_function(rhm_whm_same_hm_diff_ub, bitwidths, matsizes),
        "rhm_whm_same_hm_same_ub": test_function(rhm_whm_same_hm_same_ub, bitwidths, matsizes)
    }

# from HM0 to UB0 and from UB1 to HM1 (no overlap in HM or UB)
# setup preloads something into UB 1 for WHM to read from.
# instrs write HM 0 to UB 0 and then write UB 1 to HM 1.
def rhm_whm_diff_hm_diff_ub(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 2 1 1"],
                       instrs=[f"RHM 0 0 {L1}", f"WHM 1 1 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rhm_whm_diff_hm_diff_ub",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# from HM0 to UB0 and from UB0 to HM1 (same UB)
# setup is not needed to test that the main instructions move data to UB and
#     back to HM in a different slot (1).
# instrs write HM 0 to UB 0 and then write UB 0 to HM 1.
def rhm_whm_diff_hm_same_ub(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=[],
                       instrs=[f"RHM 0 0 {L1}", f"WHM 1 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rhm_whm_diff_hm_same_ub",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# from HM0 to UB0 and from UB1 to HM0 (same HM)
# setup writes a differnt matrix (HM2) to UB 1 to ensure that it's written to 
#     HM0.
# instrs write HM 0 to UB 0 and then write UB 1 to HM 0.
def rhm_whm_same_hm_diff_ub(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 2 1 1"],
                       instrs=[f"RHM 0 0 {L1}", f"WHM 0 1 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rhm_whm_same_hm_diff_ub",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# from HM0 to UB0 and from UB0 to HM0 (same UB and HM)
# setup writes a different matrix (HM1) to UB 0 to ensure that it's later
#     overwritten.
# instrs write HM 0 to UB 0 and then write UB 0 directly back to HM 0.
def rhm_whm_same_hm_same_ub(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 1 0 1"],
                       instrs=[f"RHM 0 0 {L1}", f"WHM 0 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rhm_whm_same_hm_same_ub",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)



### RHM-RW TESTS ###
def test_all_rhm_rw(test_function, bitwidths, matsizes):
    return {
        "rhm_rw": test_function(rhm_rw, bitwidths, matsizes)
    }

# from HM0 to UB0 and reading from RW0
# setup is not needed.
# instrs write HM 0 to UB 0 and then loads a weight into RW 0.
def rhm_rw(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=[],
                       instrs=[f"RHM 0 0 {L1}", f"RW 0"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rhm_rw",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)



### RHM-MMC TESTS ###
def test_all_rhm_mmc(test_function, bitwidths, matsizes):
    return {
        "rhm_mmc_same_ub_no_s": test_function(rhm_mmc_same_ub_no_s, bitwidths, matsizes),
        "rhm_mmc_diff_ub_no_s": test_function(rhm_mmc_diff_ub_no_s, bitwidths, matsizes),
        "rhm_mmc_same_ub_yes_s": test_function(rhm_mmc_same_ub_yes_s, bitwidths, matsizes),
        "rhm_mmc_diff_ub_yes_s": test_function(rhm_mmc_diff_ub_yes_s, bitwidths, matsizes)
    }

# from HM0 to UB0 and multiplying UB0 with ACC0, no .S (same UB)
# setup reads a weight into RW 0 for use in multiplication.
# instrs write HM0 to UB0 and then multiply UB0 with RW0 into ACC0.
def rhm_mmc_same_ub_no_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RW 0"],
                       instrs=[f"RHM 0 0 {L1}", f"MMC 0 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rhm_mmc_same_ub_no_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# from HM0 to UB0 and multiplying UB1 with ACC0, no .S (different UBs)
# setup reads a weight into RW 0 for use in multiplication and reads a matrix
#     from HM1 to UB1 for use in multiplication.
# instrs write HM0 to UB0 and then multiply UB1 with RW0 into ACC0.
def rhm_mmc_diff_ub_no_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RW 0", "RHM 1 1 1"],
                       instrs=[f"RHM 0 0 {L1}", f"MMC 0 1 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rhm_mmc_diff_ub_no_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# from HM0 to UB0 and multiplying UB0 with ACC0, w/ .S (same UB)
# setup reads a weight into RW 0 and RW 1 (to make sure it switches after MMC).
# instrs write HM0 to UB0 and then multiply UB0 with RW0 into ACC0 with .S.
def rhm_mmc_same_ub_yes_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RW 0", "RW 1"],
                       instrs=[f"RHM 0 0 {L1}", f"MMC.S 0 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rhm_mmc_same_ub_yes_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# from HM0 to UB0 and multiplying UB1 with ACC0, w/ .S (different UBs)
# setup reads a weight into RW 0 and RW 1 (to make sure it switches after MMC)
#     and reads a matrix from HM1 to UB1 for use in multiplication.
# instrs write HM0 to UB0 and multiplies UB1 with RW0 into ACC0 with .S.
def rhm_mmc_diff_ub_yes_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RW 0", "RW 1", "RHM 1 1 1"],
                       instrs=[f"RHM 0 0 {L1}", f"MMC.S 0 1 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rhm_mmc_diff_ub_yes_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)



### RHM-ACT TESTS ###
def test_all_rhm_act(test_function, bitwidths, matsizes):
    return {
        "rhm_act_same_ub": test_function(rhm_act_same_ub, bitwidths, matsizes),
        "rhm_act_diff_ub": test_function(rhm_act_diff_ub, bitwidths, matsizes)
    }

# from HM0 to UB0 and accumulate from ACC0 to UB0 (same UB)
# setup reads HM1 into UB1 and reads RW0 into the weight queue, and multiplies
#     them into ACC0.
# instrs write HM0 to UB0 and then accumulate from ACC0 to UB0, overwriting the
#     existing data.
def rhm_act_same_ub(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 1 1 1", "RW 0", "MMC 0 1 1"],
                       instrs=[f"RHM 0 0 {L1}", f"ACT 0 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rhm_act_same_ub",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# from HM0 to UB0 and accumulate from ACC0 to UB1 (different UBs)
# setup reads HM1 into UB1, reads RW0 into the weight queue, and multiplies
#     them into ACC0.
# instrs write HM0 to UB0 and then accumulate from ACC0 to UB1.
def rhm_act_diff_ub(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 1 1 1", "RW 0", "MMC 0 1 1"],
                       instrs=[f"RHM 0 0 {L1}", f"ACT 0 1 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rhm_act_diff_ub",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)



### RHM-HLT TESTS ###
def test_all_rhm_hlt(test_function, bitwidths, matsizes):
    return {
        "rhm_hlt": test_function(rhm_hlt, bitwidths, matsizes)
    }

# from HM0 to UB0 and halting
# setup is not needed.
# instrs write HM 0 to UB 0 and then halt.
def rhm_hlt(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=[],
                       instrs=[f"RHM 0 0 {L1}", f"HLT"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rhm_hlt",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)



### WHM-RHM TESTS ###
def test_all_whm_rhm(test_function, bitwidths, matsizes):
    return {
        "whm_rhm_diff_hm_diff_ub": test_function(whm_rhm_diff_hm_diff_ub, bitwidths, matsizes),
        "whm_rhm_diff_hm_same_ub": test_function(whm_rhm_diff_hm_same_ub, bitwidths, matsizes),
        "whm_rhm_same_hm_diff_ub": test_function(whm_rhm_same_hm_diff_ub, bitwidths, matsizes),
        "whm_rhm_same_hm_same_ub": test_function(whm_rhm_same_hm_same_ub, bitwidths, matsizes)
    }

# from UB0 to HM0 and from HM1 to UB1 (no overlap in HM or UB)
# setup writes a matrix from HM2 to UB0
# instrs write from UB0 to HM0 and from HM1 to UB1
def whm_rhm_diff_hm_diff_ub(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 2 0 1"],
                       instrs=[f"WHM 0 0 {L1}", f"RHM 1 1 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="whm_rhm_diff_hm_diff_ub",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# from UB0 to HM0 and from HM1 to UB0 (same UB)
# setup writes a matrix from HM2 to UB0 so that it has content to start with
# instrs write from UB0 to HM0 and from HM1 to UB0
def whm_rhm_diff_hm_same_ub(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 2 0 1"],
                       instrs=[f"WHM 0 0 {L1}", f"RHM 1 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="whm_rhm_diff_hm_same_ub",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# from UB0 to HM0 and from HM0 to UB1 (same HM)
# setup writes a matrix from HM1 to UB1 so that it has content to start with
# instrs write from UB0 to HM0 and from HM0 to UB1
def whm_rhm_same_hm_diff_ub(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 1 0 1"],
                       instrs=[f"WHM 0 0 {L1}", f"RHM 0 1 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="whm_rhm_same_hm_diff_ub",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# from UB0 to HM0 and from HM0 to UB0 (same UB and HM)
# setup writes a matrix from HM1 to UB0 so that it has content to start with
# instrs write from UB0 to HM0 and from HM0 to UB0
def whm_rhm_same_hm_same_ub(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 1 0 1"],
                       instrs=[f"WHM 0 0 {L1}", f"RHM 0 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="whm_rhm_same_hm_same_ub",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)



### WHM-WHM TESTS ###
def test_all_whm_whm(test_function, bitwidths, matsizes):
    return {
        "whm_whm_diff_hm_diff_ub": test_function(whm_whm_diff_hm_diff_ub, bitwidths, matsizes),
        "whm_whm_same_hm_diff_ub": test_function(whm_whm_same_hm_diff_ub, bitwidths, matsizes),
        "whm_whm_diff_hm_same_ub": test_function(whm_whm_diff_hm_same_ub, bitwidths, matsizes),
        "whm_whm_same_hm_same_ub": test_function(whm_whm_same_hm_same_ub, bitwidths, matsizes)
    }

# from UB0 to HM0 and from UB1 to HM1 (no overlap in HM or UB)
# setup writes matrices from HM2 to UB0 and from HM3 to UB1 to get different 
#     values in them.
# instrs write from UB0 to HM0 and from UB1 to HM1
def whm_whm_diff_hm_diff_ub(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 2 0 1", "RHM 3 1 1"],
                       instrs=[f"WHM 0 0 {L1}", f"WHM 1 1 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="whm_whm_diff_hm_diff_ub",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# from UB0 to HM0 and from UB1 to HM0 (same destination in HM)
# setup writes matrices from HM1 to UB0 and from HM2 to UB1 to get different
#     values in them.
# instrs write from UB0 to HM0 and then write from UB1 to HM0
def whm_whm_same_hm_diff_ub(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 1 0 1", "RHM 2 1 1"],
                       instrs=[f"WHM 0 0 {L1}", f"WHM 0 1 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="whm_whm_same_hm_diff_ub",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# from UB0 to HM0 and from UB0 to HM1 (same origin in UB)
# setup writes a matrix from HM2 to UB0 to gett different values in it.
# instrs write from UB0 to HM0 and HM1.
def whm_whm_diff_hm_same_ub(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 2 0 1"],
                       instrs=[f"WHM 0 0 {L1}", f"WHM 1 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="whm_whm_diff_hm_same_ub",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# from UB0 to HM0 and from UB0 to HM0 (same origin in UB and destination in HM)
# setup writes a matrix from HM1 to UB0 to get different values in it.
# instrs write from UB0 to HM0 and then write from UB0 to HM0 again
def whm_whm_same_hm_same_ub(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 1 0 1"],
                       instrs=[f"WHM 0 0 {L1}", f"WHM 0 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="whm_whm_same_hm_same_ub",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)



### WHM-RW TESTS ###
def test_all_whm_rw(test_function, bitwidths, matsizes):
    return {
        "whm_rw": test_function(whm_rw, bitwidths, matsizes)
    }

# from UB0 to HM0 and reading from RW0
# setup writes a matrix from HM1 to UB0 to put a value in it and prepares for
#     matmul by loading HM2 into UB1. 
# instrs write from UB0 to HM0 and then load a weight into RW0.
def whm_rw(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 1 0 1", "RHM 2 1 1"],
                       instrs=[f"WHM 0 0 {L1}", "RW 0"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="whm_rw",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)



### WHM-MMC TESTS ###
def test_all_whm_mmc(test_function, bitwidths, matsizes):
    return {
        "whm_mmc_same_ub_no_s": test_function(whm_mmc_same_ub_no_s, bitwidths, matsizes),
        "whm_mmc_diff_ub_no_s": test_function(whm_mmc_diff_ub_no_s, bitwidths, matsizes),
        "whm_mmc_same_ub_yes_s": test_function(whm_mmc_same_ub_yes_s, bitwidths, matsizes),
        "whm_mmc_diff_ub_yes_s": test_function(whm_mmc_diff_ub_yes_s, bitwidths, matsizes)
    }

# from UB0 to HM0 and multiplying UB0 into ACC0, no .S (same UB)
# setup loads HM1 into UB0 so that it has a value, and loads RW0 and RW1 into
#     the weight queue.
# instrs write from UB0 to HM0 and then multiply UB0 into ACC0.
def whm_mmc_same_ub_no_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 1 0 1", "RW 0", "RW 1"],
                       instrs=[f"WHM 0 0 {L1}", f"MMC 0 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="whm_mmc_same_ub_no_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# from UB0 to HM0 and multiplying UB1 into ACC0, no .S (different UBs)
# setup loads HM1 into UB1 so that it has a value, and loads RW0 and RW1 into
#     the weight queue.
# instrs write from UB0 to HM0 and then multiply UB1 into ACC0.
def whm_mmc_diff_ub_no_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 1 1 1", "RW 0", "RW 1"],
                       instrs=[f"WHM 0 0 {L1}", f"MMC 0 1 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="whm_mmc_diff_ub_no_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# from UB0 to HM0 and multiplying UB0 into ACC0, w/ .S (same UB)
# setup loads HM1 into UB0 so that it has a value, and loads RW0 and RW1 into
#     the weight queue.
# instrs write from UB0 to HM0 and then multiply UB0 into ACC0.
def whm_mmc_same_ub_yes_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 1 0 1", "RW 0", "RW 1"],
                       instrs=[f"WHM 0 0 {L1}", f"MMC.S 0 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="whm_mmc_same_ub_yes_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# from UB0 to HM0 and multiplying UB1 into ACC0, w/ .S (different UBs)
# setup loads HM1 into UB1 so that it has a value, and loads RW0 and RW1 into
#     the weight queue.
# instrs write from UB0 to HM0 and then multiply UB1 into ACC0.
def whm_mmc_diff_ub_yes_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 1 1 1", "RW 0", "RW 1"],
                       instrs=[f"WHM 0 0 {L1}", f"MMC.S 0 1 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="whm_mmc_diff_ub_yes_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)



### WHM-ACT TESTS ###
def test_all_whm_act(test_function, bitwidths, matsizes):
    return {
        "whm_act_same_ub": test_function(whm_act_same_ub, bitwidths, matsizes),
        "whm_act_diff_ub": test_function(whm_act_diff_ub, bitwidths, matsizes)
    }

# from UB0 to HM0 and accumulate from ACC0 to UB0 (same UB)
# setup loads HM1 into UB1 so that it has a value, loads RW0 into the weight
#     matrix, and performs the multiplication into ACC0.
# instrs write from UB0 to HM0 and then accumulate from ACC0 to UB0.
def whm_act_same_ub(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 1 1 1", "RW 0", "MMC 0 1 1"],
                       instrs=[f"WHM 0 0 {L1}", f"ACT 0 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="whm_act_same_ub",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# from UB0 to HM0 and accumulate from ACC0 to UB1 (different UBs)
# setup loads HM3 into UB0 so that it has a value, loads HM2 into UB2, loads
#     RW0 into the weight queue, and multiplies UB2 with RW0 into ACC0.
# instrs write from UB0 to HM0 and then accumulate from ACC0 to UB1.
def whm_act_diff_ub(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 3 0 1", "RHM 2 2 1", "RW 0", "MMC 0 2 1"],
                       instrs=[f"WHM 0 0 {L1}", f"ACT 0 1 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="whm_act_diff_ub",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)



### WHM-HLT TESTS ###
def test_all_whm_hlt(test_function, bitwidths, matsizes):
    return {
        "whm_hlt": test_function(whm_hlt, bitwidths, matsizes)
    }

# from UB0 to HM0 and halting
# setup writes a matrix from HM1 to UB0 to put a value in it. 
# instrs write from UB0 to HM0 and then halt.
def whm_hlt(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 1 0 1"],
                       instrs=[f"WHM 0 0 {L1}", "HLT"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="whm_hlt",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)



### RW-RHM TESTS ###
def test_all_rw_rhm(test_function, bitwidths, matsizes):
    return {
        "rw_rhm": test_function(rw_rhm, bitwidths, matsizes)
    }

# reading from RW0 and moving from HM0 to UB0
# setup not needed.
# instrs load a weight into RW0 and then move a matrix from HM0 to UB0
def rw_rhm(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=[],
                       instrs=["RW 0", f"RHM 0 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rw_rhm",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)



### RW-WHM TESTS ###
def test_all_rw_whm(test_function, bitwidths, matsizes):
    return {
        "rw_whm": test_function(rw_whm, bitwidths, matsizes)
    }

# reading from RW0 and moving from UB0 to HM0
# setup loads a matrix from HM1 into UB0 so that it has a value.
# instrs load a weight into RW0 and then move a matrix from UB0 to HM0.
def rw_whm(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 1 0 1"],
                       instrs=["RW 0", f"WHM 0 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rw_whm",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)



### RW-RW TESTS ###
def test_all_rw_rw(test_function, bitwidths, matsizes):
    return {
        "rw_rw_same_weights_empty": test_function(rw_rw_same_weights_empty, bitwidths, matsizes),
        "rw_rw_diff_weights_empty": test_function(rw_rw_diff_weights_empty, bitwidths, matsizes),
        # "rw_rw_same_weights_one_space": test_function(rw_rw_same_weights_one_space, bitwidths, matsizes), # 5 consecutive RWs
        # "rw_rw_diff_weights_one_space": test_function(rw_rw_diff_weights_one_space, bitwidths, matsizes), # 5 consecutive RWs
        # "rw_rw_same_weights_full": test_function(rw_rw_same_weights_full, bitwidths, matsizes), # 6 consecutive RWs
        # "rw_rw_diff_weights_full": test_function(rw_rw_diff_weights_full, bitwidths, matsizes) # 6 consecutive RWs
    }

# reading from RW0 and RW0, buffer starts empty (same weights)
# setup not needed.
# instrs load RW0 into the weight queue and then load RW0 again.
def rw_rw_same_weights_empty(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=[],
                       instrs=["RW 0", "RW 0"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rw_rw_same_weights_empty",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# reading from RW0 and RW1, buffer starts empty (different weights)
# setup not needed.
# instrs load RW0 into the weight queue and then load RW1.
def rw_rw_diff_weights_empty(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=[],
                       instrs=["RW 0", "RW 1"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rw_rw_diff_weights_empty",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# reading from RW0 and RW0, buffer starts with one space (same weights)
# setup reads RW0, RW1, and RW2 into the weight queue so that there's one slot
#     remaining.
# instrs load RW3 into the weight queue and then load RW3 again.
def rw_rw_same_weights_one_space(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RW 0", "RW 1", "RW 2"],
                       instrs=["RW 3", "RW 3"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rw_rw_same_weights_one_space",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# reading from RW0 and RW1, buffer starts with one space (different weights)
# setup reads RW0, RW1, and RW2 into the weight queue so that there's one slot
#     remaining.
# instrs load RW3 into the weight queue and then load RW4.
def rw_rw_diff_weights_one_space(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RW 0", "RW 1", "RW 2"],
                       instrs=["RW 3", "RW 4"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rw_rw_diff_weights_one_space",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# reading from RW0 and RW0, buffer starts full (same weights)
# setup reads RW0, RW1, RW2, and RW3 into the weight queue so that there's one 
#     slot remaining.
# instrs load RW4 into the weight queue and then load RW4 again.
def rw_rw_same_weights_full(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RW 0", "RW 1", "RW 2", "RW 3"],
                       instrs=["RW 4", "RW 4"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rw_rw_same_weights_full",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# reading from RW0 and RW1, buffer starts full (different weights)
# setup reads RW0, RW1, RW2, and RW3 into the weight queue so that there's one 
#     slot remaining.
# instrs load RW4 into the weight queue and then load RW5.
def rw_rw_diff_weights_full(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RW 0", "RW 1", "RW 2", "RW 3"],
                       instrs=["RW 4", "RW 5"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rw_rw_diff_weights_full",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)



### RW-MMC TESTS ###
def test_all_rw_mmc(test_function, bitwidths, matsizes):
    return {
        "rw_mmc_empty_no_s": test_function(rw_mmc_empty_no_s, bitwidths, matsizes),
        "rw_mmc_empty_yes_s": test_function(rw_mmc_empty_yes_s, bitwidths, matsizes),
        "rw_mmc_one_space_no_s": test_function(rw_mmc_one_space_no_s, bitwidths, matsizes),
        "rw_mmc_one_space_yes_s": test_function(rw_mmc_one_space_yes_s, bitwidths, matsizes),
        # "rw_mmc_full_no_s": test_function(rw_mmc_full_no_s, bitwidths, matsizes), # 5 consecutive RWs
        # "rw_mmc_full_yes_s": test_function(rw_mmc_full_yes_s, bitwidths, matsizes) # 5 consecutive RWs
    }

# reading from RW0, buffer starts empty, multiplying UB0 into ACC0, no .S
# setup reads HM0 into UB0.
# instrs load RW0 into the weight queue and then multiply UB0 and RW0 into ACC0.
def rw_mmc_empty_no_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1"],
                       instrs=["RW 0", f"MMC 0 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rw_mmc_empty_no_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# reading from RW0, buffer starts empty, multiplying UB0 into ACC0, w/ .S
# setup reads HM0 into UB0.
# instrs load RW0 into the weight queue and then multiply UB0 and RW0 into ACC0.
def rw_mmc_empty_yes_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1"],
                       instrs=["RW 0", f"MMC.S 0 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rw_mmc_empty_yes_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# reading from RW0, buffer starts with one space, multiplying UB0 into ACC0, no .S
# setup reads RW0, RW1, and RW2 into the weight queue so that there's one slot
#     remaining. it also reads HM0 into UB0.
# instrs load RW3 into the weight queue and then multiply UB0 and RW0 into ACC0.
def rw_mmc_one_space_no_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1", "RW 0", "RW 1", "RW 2"],
                       instrs=["RW 3", f"MMC 0 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rw_mmc_one_space_no_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# reading from RW0, buffer starts with one space, multiplying UB0 into ACC0, w/ .S
# setup reads RW0, RW1, and RW2 into the weight queue so that there's one slot
#     remaining. it also reads HM0 into UB0.
# instrs load RW3 into the weight queue and then multiply UB0 and RW0 into ACC0.
def rw_mmc_one_space_yes_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1", "RW 0", "RW 1", "RW 2"],
                       instrs=["RW 3", f"MMC.S 0 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rw_mmc_one_space_yes_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# reading from RW0, buffer starts full, multiplying UB0 into ACC0, no .S
# setup reads RW0, RW1, RW2, and RW3 into the weight queue so that there's no
#     space remaining. it also reads HM0 into UB0.
# instrs load RW4 into the weight queue and then multiply UB0 and RW0 into ACC0.
def rw_mmc_full_no_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1", "RW 0", "RW 1", "RW 2", "RW 3"],
                       instrs=["RW 4", f"MMC 0 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rw_mmc_full_no_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# reading from RW0, buffer starts full, multiplying UB0 into ACC0, w/ .S
# setup reads RW0, RW1, RW2, and RW3 into the weight queue so that there's no
#     space remaining. it also reads HM0 into UB0.
# instrs load RW4 into the weight queue and then multiply UB0 and RW0 into ACC0.
def rw_mmc_full_yes_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1", "RW 0", "RW 1", "RW 2", "RW 3"],
                       instrs=["RW 4", f"MMC.S 0 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rw_mmc_full_yes_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)



### RW-ACT TESTS ###
def test_all_rw_act(test_function, bitwidths, matsizes):
    return {
        "rw_act": test_function(rw_act, bitwidths, matsizes)
    }

# reading from RW0 and accumulate from ACC0 to UB0
# setup reads HM1 into UB1 so that it has a value, loads RW0, and multiplies
#     them into ACC0 while switching weights. 
# instrs load RW1 into the weight queue and then accumulate from ACC0 to UB0.
def rw_act(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 1 1 1", "RW 0", "MMC.S 0 1 1"],
                       instrs=["RW 1", f"ACT 0 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rw_act",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)



### RW-HLT TESTS ###
def test_all_rw_hlt(test_function, bitwidths, matsizes):
    return {
        "rw_hlt_empty": test_function(rw_hlt_empty, bitwidths, matsizes),
        "rw_hlt_one_space": test_function(rw_hlt_one_space, bitwidths, matsizes),
        # "rw_hlt_full": test_function(rw_hlt_full, bitwidths, matsizes) # 5 consecutive RWs
    }

# reading from RW0 and halting, buffer starts empty
# setup not needed.
# instrs load RW0 into the weight queue and then halt.
def rw_hlt_empty(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=[],
                       instrs=["RW 0", "HLT"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rw_hlt_empty",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# reading from RW0 and halting, buffer starts with one space
# setup reads RW0, RW1, and RW2 into the weight queue so that there's one slot
#     remaining.
# instrs load RW3 into the weight queue and then halt.
def rw_hlt_one_space(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RW 0", "RW 1", "RW 2"],
                       instrs=["RW 3", "HLT"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rw_hlt_one_space",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# reading from RW0 and halting, buffer starts full
# setup reads RW0, RW1, RW2, and RW3 into the weight queue so that there's no 
#     slots remaining.
# instrs load RW4 into the weight queue and then halt.
def rw_hlt_full(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RW 0", "RW 1", "RW 2", "RW 3"],
                       instrs=["RW 4", "HLT"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rw_hlt_full",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)



### MMC-RHM TESTS ###
def test_all_mmc_rhm(test_function, bitwidths, matsizes):
    return {
        "mmc_rhm_same_ub_no_s": test_function(mmc_rhm_same_ub_no_s, bitwidths, matsizes),
        "mmc_rhm_same_ub_yes_s": test_function(mmc_rhm_same_ub_yes_s, bitwidths, matsizes),
        "mmc_rhm_diff_ub_no_s": test_function(mmc_rhm_diff_ub_no_s, bitwidths, matsizes),
        "mmc_rhm_diff_ub_yes_s": test_function(mmc_rhm_diff_ub_yes_s, bitwidths, matsizes)
    }

# multiplying UB0 into ACC0, no .S, moving from HM0 to UB0 (same UB)
# setup reads HM1 into UB0 so that it has a value, loads RW0, and loads RW1.
# instrs multiply UB0 with RW0 into ACC0 and then move a matrix from HM0 to UB0.
def mmc_rhm_same_ub_no_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 1 0 1", "RW 0", "RW 1"],
                       instrs=[f"MMC 0 0 {L1}", f"RHM 0 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_rhm_same_ub_no_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# multiplying UB0 into ACC0, w/ .S, moving from HM0 to UB0 (same UB)
# setup reads HM1 into UB0 so that it has a value, loads RW0, and loads RW1.
# instrs multiply UB0 with RW0 into ACC0 and then move a matrix from HM0 to UB0.
def mmc_rhm_same_ub_yes_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 1 0 1", "RW 0", "RW 1"],
                       instrs=[f"MMC.S 0 0 {L1}", f"RHM 0 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_rhm_same_ub_yes_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# multiplying UB0 into ACC0, no .S, moving from HM0 to UB1 (different UB)
# setup reads HM1 into UB0 so that it has a value, loads RW0, and loads RW1.
# instrs multiply HM0 with RW0 into ACC0 and then move a matrix from HM0 to UB1.
def mmc_rhm_diff_ub_no_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 1 0 1", "RW 0", "RW 1"],
                       instrs=[f"MMC 0 0 {L1}", f"RHM 0 1 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_rhm_diff_ub_no_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# multiplying UB0 into ACC0, w/ .S, moving from HM0 to UB1 (different UB)
# setup reads HM1 into UB0 so that it has a value, loads RW0, and loads RW1.
# instrs multiply HM0 with RW0 into ACC0 and then move a matrix from HM0 to UB1.
def mmc_rhm_diff_ub_yes_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 1 0 1", "RW 0", "RW 1"],
                       instrs=[f"MMC.S 0 0 {L1}", f"RHM 0 1 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_rhm_diff_ub_yes_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)



### MMC-WHM TESTS ###
def test_all_mmc_whm(test_function, bitwidths, matsizes):
    return {
        "mmc_whm_same_ub_no_s": test_function(mmc_whm_same_ub_no_s, bitwidths, matsizes),
        "mmc_whm_same_ub_yes_s": test_function(mmc_whm_same_ub_yes_s, bitwidths, matsizes),
        "mmc_whm_diff_ub_no_s": test_function(mmc_whm_diff_ub_no_s, bitwidths, matsizes),
        "mmc_whm_diff_ub_yes_s": test_function(mmc_whm_diff_ub_yes_s, bitwidths, matsizes)
    }

# multiplying UB0 into ACC0, no .S, moving from UB0 to HM0 (same UB)
# setup reads HM1 into UB0 so that it has a different value, loads RW0 and RW1.
# instrs multiply UB0 with RW0 into ACC0 and then move a matrix from UB0 to HM0.
def mmc_whm_same_ub_no_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 1 0 1", "RW 0", "RW 1"],
                       instrs=[f"MMC 0 0 {L1}", f"WHM 0 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_whm_same_ub_no_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# multiplying UB0 into ACC0, w/ .S, moving from UB0 to HM0 (same UB)
# setup reads HM1 into UB0 so that it has a different value, loads RW0 and RW1.
# instrs multiply UB0 with RW0 into ACC0 and then move a matrix from UB0 to HM0.
def mmc_whm_same_ub_yes_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 1 0 1", "RW 0", "RW 1"],
                       instrs=[f"MMC.S 0 0 {L1}", f"WHM 0 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_whm_same_ub_yes_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# multiplying UB0 into ACC0, no .S, moving from UB0 to HM1 (different UB)
# setup reads HM1 into UB0 and HM2 into UB1 and loads RW0 and RW1.
# instrs multiply UB0 with RW0 into ACC0 and then move a matrix from UB1 to HM0.
def mmc_whm_diff_ub_no_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 1 0 1", "RHM 2 1 1", "RW 0", "RW 1"],
                       instrs=[f"MMC 0 0 {L1}", f"WHM 0 1 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_whm_diff_ub_no_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# multiplying UB0 into ACC0, w/ .S, moving from UB1 to HM0 (different UB)
# setup reads HM1 into UB0 and HM2 into UB1 and loads RW0 and RW1.
# instrs multiply UB0 with RW0 into ACC0 and then move a matrix from UB1 to HM0.
def mmc_whm_diff_ub_yes_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 1 0 1", "RHM 2 1 1", "RW 0", "RW 1"],
                       instrs=[f"MMC.S 0 0 {L1}", f"WHM 0 1 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_whm_diff_ub_yes_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)



### MMC-RW TESTS ###
def test_all_mmc_rw(test_function, bitwidths, matsizes):
    return {
        # "mmc_rw_empty_no_s": test_function(mmc_rw_empty_no_s, bitwidths, matsizes), # MMC with empty queue
        # "mmc_rw_empty_yes_s": test_function(mmc_rw_empty_yes_s, bitwidths, matsizes), # MMC with empty queue
        "mmc_rw_one_space_no_s": test_function(mmc_rw_one_space_no_s, bitwidths, matsizes),
        "mmc_rw_one_space_yes_s": test_function(mmc_rw_one_space_yes_s, bitwidths, matsizes), # shortened cleanup to avoid empty queue MMC
        # "mmc_rw_full_no_s": test_function(mmc_rw_full_no_s, bitwidths, matsizes), # overloads queue with 5 MMCs
        "mmc_rw_full_yes_s": test_function(mmc_rw_full_yes_s, bitwidths, matsizes)
    }

# multiplying UB0 into ACC0, no .S, reading from RW0, buffer starts empty
# setup reads HM0 into UB0. 
# instrs multiply UB0 with the fifo queue into ACC0 when there's nothing in the 
#     FIFO queue. Then load RW0 into the FIFO queue.
def mmc_rw_empty_no_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1"],
                       instrs=[f"MMC 0 0 {L1}", "RW 0"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_rw_empty_no_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# multiplying UB0 into ACC0, w/ .S, reading from RW0, buffer starts empty
# setup reads HM0 into UB0. 
# instrs multiply UB0 with the fifo queue into ACC0 when there's nothing in the 
#     FIFO queue. Then load RW0 into the FIFO queue.
def mmc_rw_empty_yes_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1"],
                       instrs=[f"MMC.S 0 0 {L1}", "RW 0"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_rw_empty_yes_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# multiplying UB0 into ACC0, no .S, reading from RW0, buffer starts with one space
# setup reads RW0, RW1, and RW2 into the FIFO queue so that there's one slot 
#     left. it also reads HM0 into UB0.
# instrs multiply UB0 with the fifo queue into ACC0. Then load RW3 into the 
#     queue.
def mmc_rw_one_space_no_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RW 0", "RW 1", "RW 2", "RHM 0 0 1"],
                       instrs=[f"MMC 0 0 {L1}", "RW 3"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_rw_one_space_no_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# multiplying UB0 into ACC0, w/ .S, reading from RW0, buffer starts with one space
# setup reads RW0, RW1, and RW2 into the FIFO queue so that there's one slot 
#     left. it also reads HM0 into UB0.
# instrs multiply UB0 with the fifo queue into ACC0. Then load RW3 into the 
#     queue.
def mmc_rw_one_space_yes_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RW 0", "RW 1", "RW 2", "RHM 0 0 1"],
                       instrs=[f"MMC.S 0 0 {L1}", "RW 3"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_rw_one_space_yes_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# multiplying UB0 into ACC0, no .S, reading from RW0, buffer starts full
# setup reads RW0, RW1, RW2, and RW3 into the FIFO queue so that there's no 
#     space left. it also reads HM0 into UB0.
# instrs multiply UB0 with the fifo queue into ACC0. Then load RW4 into the
#     queue.
def mmc_rw_full_no_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RW 0", "RW 1", "RW 2", "RW 3", "RHM 0 0 1"],
                       instrs=[f"MMC 0 0 {L1}", "RW 4"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_rw_full_no_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# multiplying UB0 into ACC0, w/ .S, reading from RW0, buffer starts full
# setup reads RW0, RW1, RW2, and RW3 into the FIFO queue so that there's no 
#     space left. it also reads HM0 into UB0.
# instrs multiply UB0 with the fifo queue into ACC0. Then load RW4 into the
#     queue.
def mmc_rw_full_yes_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RW 0", "RW 1", "RW 2", "RW 3", "RHM 0 0 1"],
                       instrs=[f"MMC.S 0 0 {L1}", "RW 4"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_rw_full_yes_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)



### MMC-MMC TESTS ###
def test_all_mmc_mmc(test_function, bitwidths, matsizes):
    return {
        "mmc_mmc_diff_ub_diff_acc_no_s_no_s": test_function(mmc_mmc_diff_ub_diff_acc_no_s_no_s, bitwidths, matsizes),
        "mmc_mmc_diff_ub_diff_acc_no_s_yes_s": test_function(mmc_mmc_diff_ub_diff_acc_no_s_yes_s, bitwidths, matsizes),
        "mmc_mmc_diff_ub_diff_acc_yes_s_no_s": test_function(mmc_mmc_diff_ub_diff_acc_yes_s_no_s, bitwidths, matsizes),
        "mmc_mmc_diff_ub_diff_acc_yes_s_yes_s": test_function(mmc_mmc_diff_ub_diff_acc_yes_s_yes_s, bitwidths, matsizes),
        "mmc_mmc_same_ub_diff_acc_no_s_no_s": test_function(mmc_mmc_same_ub_diff_acc_no_s_no_s, bitwidths, matsizes),
        "mmc_mmc_same_ub_diff_acc_no_s_yes_s": test_function(mmc_mmc_same_ub_diff_acc_no_s_yes_s, bitwidths, matsizes),
        "mmc_mmc_same_ub_diff_acc_yes_s_no_s": test_function(mmc_mmc_same_ub_diff_acc_yes_s_no_s, bitwidths, matsizes),
        "mmc_mmc_same_ub_diff_acc_yes_s_yes_s": test_function(mmc_mmc_same_ub_diff_acc_yes_s_yes_s, bitwidths, matsizes),
        "mmc_mmc_diff_ub_same_acc_no_s_no_s": test_function(mmc_mmc_diff_ub_same_acc_no_s_no_s, bitwidths, matsizes),
        "mmc_mmc_diff_ub_same_acc_no_s_yes_s": test_function(mmc_mmc_diff_ub_same_acc_no_s_yes_s, bitwidths, matsizes),
        "mmc_mmc_diff_ub_same_acc_yes_s_no_s": test_function(mmc_mmc_diff_ub_same_acc_yes_s_no_s, bitwidths, matsizes),
        "mmc_mmc_diff_ub_same_acc_yes_s_yes_s": test_function(mmc_mmc_diff_ub_same_acc_yes_s_yes_s, bitwidths, matsizes),
        "mmc_mmc_same_ub_same_acc_no_s_no_s": test_function(mmc_mmc_same_ub_same_acc_no_s_no_s, bitwidths, matsizes),
        "mmc_mmc_same_ub_same_acc_no_s_yes_s": test_function(mmc_mmc_same_ub_same_acc_no_s_yes_s, bitwidths, matsizes),
        "mmc_mmc_same_ub_same_acc_yes_s_no_s": test_function(mmc_mmc_same_ub_same_acc_yes_s_no_s, bitwidths, matsizes),
        "mmc_mmc_same_ub_same_acc_yes_s_yes_s": test_function(mmc_mmc_same_ub_same_acc_yes_s_yes_s, bitwidths, matsizes),
    }

# multiplying UB0 into ACC0 no .S, multiplying UB1 into ACC1 no .S (different UB and ACC)
# setup reads HM0 into UB0 and HM1 into UB1. it also loads RW0 and RW1 into the
#     weight queue.
# instrs multiply UB0 with RW0 into ACC0 (no S) and UB1 with RW1 into ACC1 
#     (no S).
def mmc_mmc_diff_ub_diff_acc_no_s_no_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1", "RHM 1 1 1", "RW 0", "RW 1"],
                       instrs=[f"MMC 0 0 {L1}", f"MMC 1 1 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_mmc_diff_ub_diff_acc_no_s_no_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# multiplying UB0 into ACC0 no .S, multiplying UB1 into ACC1 w/ .S (different UB and ACC)
# setup reads HM0 into UB0 and HM1 into UB1. it also loads RW0 and RW1 into the
#     weight queue.
# instrs multiply UB0 with RW0 into ACC0 (no S) and UB1 with RW1 into ACC1
#     (with S).
def mmc_mmc_diff_ub_diff_acc_no_s_yes_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1", "RHM 1 1 1", "RW 0", "RW 1"],
                       instrs=[f"MMC 0 0 {L1}", f"MMC.S 1 1 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_mmc_diff_ub_diff_acc_no_s_yes_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# multiplying UB0 into ACC0 w/ .S, multiplying UB1 into ACC1 no .S (different UB and ACC)
# setup reads HM0 into UB0 and HM1 into UB1. it also loads RW0 and RW1 into the
#     weight queue.
# instrs multiply UB0 with RW0 into ACC0 (with S) and UB1 with RW1 into ACC1
#     (no S).
def mmc_mmc_diff_ub_diff_acc_yes_s_no_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1", "RHM 1 1 1", "RW 0", "RW 1"],
                       instrs=[f"MMC.S 0 0 {L1}", f"MMC 1 1 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_mmc_diff_ub_diff_acc_yes_s_no_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# multiplying UB0 into ACC0 w/ .S, multiplying UB1 into ACC1 w/ .S (different UB and ACC)
# setup reads HM0 into UB0 and HM1 into UB1. it also loads RW0, RW1, and RW2 
#     into the weight queue.
# instrs multiply UB0 with RW0 into ACC0 (with S) and UB1 with RW1 into ACC1
#     (with S).
def mmc_mmc_diff_ub_diff_acc_yes_s_yes_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1", "RHM 1 1 1", "RW 0", "RW 1", "RW 2"],
                       instrs=[f"MMC.S 0 0 {L1}", f"MMC.S 1 1 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_mmc_diff_ub_diff_acc_yes_s_yes_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# multiplying UB0 into ACC0 no .S, multiplying UB0 into ACC1 no .S (same UB)
# setup reads HM0 into UB0 and loads RW0 and RW1 into the weight queue.
# instrs multiply UB0 with RW0 into ACC0 (no S) and UB0 with RW0 into ACC1 
#     (no S).
def mmc_mmc_same_ub_diff_acc_no_s_no_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1", "RW 0", "RW 1"],
                       instrs=[f"MMC 0 0 {L1}", f"MMC 1 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_mmc_same_ub_diff_acc_no_s_no_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# multiplying UB0 into ACC0 no .S, multiplying UB0 into ACC1 w/ .S (same UB)
# setup reads HM0 into UB0 and loads RW0 and RW1 into the weight queue.
# instrs multiply UB0 with RW0 into ACC0 (no S) and UB0 with RW0 into ACC1 
#     (w/ S).
def mmc_mmc_same_ub_diff_acc_no_s_yes_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1", "RW 0", "RW 1"],
                       instrs=[f"MMC 0 0 {L1}", f"MMC.S 1 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_mmc_same_ub_diff_acc_no_s_yes_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# multiplying UB0 into ACC0 w/ .S, multiplying UB0 into ACC1 no .S (same UB)
# setup reads HM0 into UB0 and loads RW0 and RW1 into the weight queue.
# instrs multiply UB0 with RW0 into ACC0 (w/ S) and UB0 with RW1 into ACC1 
#     (no S).
def mmc_mmc_same_ub_diff_acc_yes_s_no_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1", "RW 0", "RW 1"],
                       instrs=[f"MMC.S 0 0 {L1}", f"MMC 1 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_mmc_same_ub_diff_acc_yes_s_no_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# multiplying UB0 into ACC0 w/ .S, multiplying UB0 into ACC1 w/ .S (same UB)
# setup reads HM0 into UB0 and loads RW0, RW1, and RW2 into the weight queue.
# instrs multiply UB0 with RW0 into ACC0 (w/ S) and UB0 with RW1 into ACC1 
#     (w/ S).
def mmc_mmc_same_ub_diff_acc_yes_s_yes_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1", "RW 0", "RW 1", "RW 2"],
                       instrs=[f"MMC.S 0 0 {L1}", f"MMC.S 1 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_mmc_same_ub_diff_acc_yes_s_yes_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# multiplying UB0 into ACC0 no .S, multiplying UB1 into ACC0 no .S (same ACC)
# setup reads HM0 and HM1 into UB0 and UB1. it also loads RW0 and RW1.
# instrs multiply UB0 with RW0 into ACC0 (no S) and UB1 with RW0 into ACC0 
#     (no S).
def mmc_mmc_diff_ub_same_acc_no_s_no_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1", "RHM 1 1 1", "RW 0", "RW 1"],
                       instrs=[f"MMC 0 0 {L1}", f"MMC 0 1 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_mmc_diff_ub_same_acc_no_s_no_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# multiplying UB0 into ACC0 no .S, multiplying UB1 into ACC0 w/ .S (same ACC)
# setup reads HM0 and HM1 into UB0 and UB1. it also loads RW0 and RW1.
# instrs multiply UB0 with RW0 into ACC0 (no S) and UB1 with RW0 into ACC0
#     (w/ S).
def mmc_mmc_diff_ub_same_acc_no_s_yes_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1", "RHM 1 1 1", "RW 0", "RW 1"],
                       instrs=[f"MMC 0 0 {L1}", f"MMC.S 0 1 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_mmc_diff_ub_same_acc_no_s_yes_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# multiplying UB0 into ACC0 w/ .S, multiplying UB1 into ACC0 no .S (same ACC)
# setup reads HM0 and HM1 into UB0 and UB1. it also loads RW0 and RW1.
# instrs multiply UB0 with RW0 into ACC0 (w/ S) and UB1 with RW1 into ACC0 
#     (no S).
def mmc_mmc_diff_ub_same_acc_yes_s_no_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1", "RHM 1 1 1", "RW 0", "RW 1"],
                       instrs=[f"MMC.S 0 0 {L1}", f"MMC 0 1 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_mmc_diff_ub_same_acc_yes_s_no_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# multiplying UB0 into ACC0 w/ .S, multiplying UB1 into ACC0 w/ .S (same ACC)
# setup reads HM0 and HM1 into UB0 and UB1. it also loads RW0, RW1, and RW2.
# instrs multiply UB0 with RW0 into ACC0 (w/ S) and UB1 with RW1 into ACC0
#     (w/ S).
def mmc_mmc_diff_ub_same_acc_yes_s_yes_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1", "RHM 1 1 1", "RW 0", "RW 1", "RW 2"],
                       instrs=[f"MMC.S 0 0 {L1}", f"MMC.S 0 1 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_mmc_diff_ub_same_acc_yes_s_yes_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# multiplying UB0 into ACC0 no .S, multiplying UB0 into ACC0 no .S (same ACC and UB)
# setup reads HM0 into UB0 and loads RW0 and RW1.
# instrs multiply UB0 with RW0 into ACC0 (no S) and UB0 with RW0 into ACC0 
#     (no S).
def mmc_mmc_same_ub_same_acc_no_s_no_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1", "RW 0", "RW 1"],
                       instrs=[f"MMC 0 0 {L1}", f"MMC 0 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_mmc_same_ub_same_acc_no_s_no_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# multiplying UB0 into ACC0 no .S, multiplying UB0 into ACC0 w/ .S (same ACC and UB)
# setup reads HM0 into UB0 and loads RW0 and RW1.
# instrs multiply UB0 with RW0 into ACC0 (no S) and UB0 with RW0 into ACC0
#     (w/ S).
def mmc_mmc_same_ub_same_acc_no_s_yes_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1", "RW 0", "RW 1"],
                       instrs=[f"MMC 0 0 {L1}", f"MMC.S 0 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_mmc_same_ub_same_acc_no_s_yes_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# multiplying UB0 into ACC0 w/ .S, multiplying UB0 into ACC0 no .S (same ACC and UB)
# setup reads HM0 into UB0 and loads RW0 and RW1.
# instrs multiply UB0 with RW0 into ACC0 (w/ S) and UB0 with RW1 into ACC0
#     (no S).
def mmc_mmc_same_ub_same_acc_yes_s_no_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1", "RW 0", "RW 1"],
                       instrs=[f"MMC.S 0 0 {L1}", f"MMC 0 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_mmc_same_ub_same_acc_yes_s_no_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# multiplying UB0 into ACC0 w/ .S, multiplying UB0 into ACC0 w/ .S (same ACC and UB)
# setup reads HM0 into UB0 and loads RW0, RW1, and RW2.
# instrs multiply UB0 with RW0 into ACC0 (w/ S) and UB0 with RW1 into ACC0
#     (w/ S).
def mmc_mmc_same_ub_same_acc_yes_s_yes_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1", "RW 0", "RW 1", "RW 2"],
                       instrs=[f"MMC.S 0 0 {L1}", f"MMC.S 0 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_mmc_same_ub_same_acc_yes_s_yes_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)



### MMC-ACT TESTS ###
def test_all_mmc_act(test_function, bitwidths, matsizes):
    return {
        "mmc_act_diff_ub_diff_acc_no_s": test_function(mmc_act_diff_ub_diff_acc_no_s, bitwidths, matsizes),
        "mmc_act_diff_ub_diff_acc_yes_s": test_function(mmc_act_diff_ub_diff_acc_yes_s, bitwidths, matsizes),
        "mmc_act_same_ub_diff_acc_no_s": test_function(mmc_act_same_ub_diff_acc_no_s, bitwidths, matsizes),
        "mmc_act_same_ub_diff_acc_yes_s": test_function(mmc_act_same_ub_diff_acc_yes_s, bitwidths, matsizes),
        "mmc_act_diff_ub_same_acc_no_s": test_function(mmc_act_diff_ub_same_acc_no_s, bitwidths, matsizes),
        "mmc_act_diff_ub_same_acc_yes_s": test_function(mmc_act_diff_ub_same_acc_yes_s, bitwidths, matsizes),
        "mmc_act_same_ub_same_acc_no_s": test_function(mmc_act_same_ub_same_acc_no_s, bitwidths, matsizes),
        "mmc_act_same_ub_same_acc_yes_s": test_function(mmc_act_same_ub_same_acc_yes_s, bitwidths, matsizes),
    }

# multiplying UB0 into ACC0 no .S, accumulate from ACC1 to UB1 (different UB and ACC)
# setup reads HM0 into UB0 and loads RW0 and RW1 into the weight queue. then it
#     loads HM3 into UB3 and multiplies UB3 with RW0 (no S) into ACC1 to prepare
#     for instr 2 to activate it.
# instrs multiply UB0 with RW0 into ACC0 (no S) and activate the result from 
#     ACC1 to UB1.
def mmc_act_diff_ub_diff_acc_no_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1", "RHM 3 3 1", "RW 0", "RW 1", 
                              "MMC 1 3 1"],
                       instrs=[f"MMC 0 0 {L1}", f"ACT 1 1 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_act_diff_ub_diff_acc_no_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# multiplying UB0 into ACC0 w/ .S, accumulate from ACC1 to UB1 (different UB and ACC)
# setup reads HM0 into UB0 and loads RW0 and RW1 into the weight queue. then it
#     loads HM3 into UB3 and multiplies UB3 with RW0 (no S) into ACC1 to prepare
#     for instr 2 to activate it.
# instrs multiply UB0 with RW0 into ACC0 (w/ S) and activate the setup result 
#     from ACC1 to UB1.
def mmc_act_diff_ub_diff_acc_yes_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1", "RHM 3 3 1", "RW 0", "RW 1", 
                              "MMC 1 3 1"],
                       instrs=[f"MMC.S 0 0 {L1}", f"ACT 1 1 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_act_diff_ub_diff_acc_yes_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# multiplying UB0 into ACC0 no .S, accumulate from ACC1 to UB0 (same UB)
# setup reads HM0 into UB0 and loads RW0 and RW1 into the weight queue. then it
#     loads HM2 into UB2 and multiplies UB2 with RW0 (no S) into ACC1 to prepare
#     for instr 2 to activate it.
# instrs multiply UB0 with RW0 into ACC0 (no S) and activate the setup result
#     from ACC1 to UB0.
def mmc_act_same_ub_diff_acc_no_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1", "RHM 2 2 1", "RW 0", "RW 1", 
                              "MMC 1 2 1"],
                       instrs=[f"MMC 0 0 {L1}", f"ACT 1 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_act_same_ub_diff_acc_no_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# multiplying UB0 into ACC0 w/ .S, accumulate from ACC1 to UB0 (same UB)
# setup reads HM0 into UB0 and loads RW0 and RW1 into the weight queue. then it
#     loads HM2 into UB2 and multiplies UB2 with RW0 (no S) into ACC1 to prepare
#     for instr 2 to activate it.
# instrs multiply UB0 with RW0 into ACC0 (w/ S) and activate the setup result
#     from ACC1 to UB0.
def mmc_act_same_ub_diff_acc_yes_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1", "RHM 2 2 1", "RW 0", "RW 1", 
                              "MMC 1 2 1"],
                       instrs=[f"MMC.S 0 0 {L1}", f"ACT 1 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_act_same_ub_diff_acc_yes_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# multiplying UB0 into ACC0 no .S, accumulate from ACC0 to UB1 (same ACC)
# setup reads HM0 into UB0 and loads RW0 and RW1 into the weight queue.
# instrs multiply UB0 with RW0 into ACC0 (no S) and write ACC0 to UB1.
def mmc_act_diff_ub_same_acc_no_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1", "RW 0", "RW 1"],
                       instrs=[f"MMC 0 0 {L1}", f"ACT 0 1 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_act_diff_ub_same_acc_no_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# multiplying UB0 into ACC0 w/ .S, accumulate from ACC0 to UB1 (same ACC)
# setup reads HM0 into UB0 and loads RW0 and RW1 into the weight queue.
# instrs multiply UB0 with RW0 into ACC0 (w/ S) and write ACC0 to UB1.
def mmc_act_diff_ub_same_acc_yes_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1", "RW 0", "RW 1"],
                       instrs=[f"MMC.S 0 0 {L1}", f"ACT 0 1 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_act_diff_ub_same_acc_yes_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# multiplying UB0 into ACC0 no .S, accumulate from ACC0 to UB0 (same ACC and UB)
# setup reads HM0 into UB0 and loads RW0 and RW1.
# instrs multiply UB0 with RW0 into ACC0 (no S) and write ACC0 back to UB0.
def mmc_act_same_ub_same_acc_no_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1", "RW 0", "RW 1"],
                       instrs=[f"MMC 0 0 {L1}", f"ACT 0 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_act_same_ub_same_acc_no_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# multiplying UB0 into ACC0 w/ .S, accumulate from ACC0 to UB0 (same ACC and UB) 
# setup reads HM0 into UB0 and loads RW0 and RW1.
# instrs multiply UB0 with RW0 into ACC0 (w/ S) and write ACC0 back to UB0.
def mmc_act_same_ub_same_acc_yes_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1", "RW 0", "RW 1"],
                       instrs=[f"MMC.S 0 0 {L1}", f"ACT 0 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_act_same_ub_same_acc_yes_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)



### MMC-HLT TESTS ###
def test_all_mmc_hlt(test_function, bitwidths, matsizes):
    return {
        # "mmc_hlt_empty_no_s": test_function(mmc_hlt_empty_no_s, bitwidths, matsizes), # MMC with empty queue
        # "mmc_hlt_empty_yes_s": test_function(mmc_hlt_empty_yes_s, bitwidths, matsizes), # MMC with empty queue
        "mmc_hlt_one_space_no_s": test_function(mmc_hlt_one_space_no_s, bitwidths, matsizes),
        "mmc_hlt_one_space_yes_s": test_function(mmc_hlt_one_space_yes_s, bitwidths, matsizes),
        "mmc_hlt_full_no_s": test_function(mmc_hlt_full_no_s, bitwidths, matsizes),
        "mmc_hlt_full_yes_s": test_function(mmc_hlt_full_yes_s, bitwidths, matsizes)
    }

# multiplying UB0 into ACC0, no .S, halting, buffer starts empty
# setup reads HM0 into UB0. 
# instrs multiply UB0 with the fifo queue into ACC0 when there's nothing in the 
#     FIFO queue. Then halt.
def mmc_hlt_empty_no_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1"],
                       instrs=[f"MMC 0 0 {L1}", "HLT"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_hlt_empty_no_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# multiplying UB0 into ACC0, w/ .S, halting, buffer starts empty
# setup reads HM0 into UB0. 
# instrs multiply UB0 with the fifo queue into ACC0 when there's nothing in the 
#     FIFO queue. Then halt.
def mmc_hlt_empty_yes_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1"],
                       instrs=[f"MMC.S 0 0 {L1}", "HLT"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_hlt_empty_yes_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# multiplying UB0 into ACC0, no .S, halting, buffer starts with one space
# setup reads RW0, RW1, and RW2 into the FIFO queue so that there's one slot 
#     left. it also reads HM0 into UB0.
# instrs multiply UB0 with the fifo queue into ACC0. Then halt.
def mmc_hlt_one_space_no_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RW 0", "RW 1", "RW 2", "RHM 0 0 1"],
                       instrs=[f"MMC 0 0 {L1}", "HLT"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_hlt_one_space_no_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# multiplying UB0 into ACC0, w/ .S, halting, buffer starts with one space
# setup reads RW0, RW1, and RW2 into the FIFO queue so that there's one slot 
#     left. it also reads HM0 into UB0.
# instrs multiply UB0 with the fifo queue into ACC0. Then halt.
def mmc_hlt_one_space_yes_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RW 0", "RW 1", "RW 2", "RHM 0 0 1"],
                       instrs=[f"MMC.S 0 0 {L1}", "HLT"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_hlt_one_space_yes_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# multiplying UB0 into ACC0, no .S, halting, buffer starts full
# setup reads RW0, RW1, RW2, and RW3 into the FIFO queue so that there's no 
#     space left. it also reads HM0 into UB0.
# instrs multiply UB0 with the fifo queue into ACC0. Then halt.
def mmc_hlt_full_no_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RW 0", "RW 1", "RW 2", "RW 3", "RHM 0 0 1"],
                       instrs=[f"MMC 0 0 {L1}", "HLT"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_hlt_full_no_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# multiplying UB0 into ACC0, w/ .S, halting, buffer starts full
# setup reads RW0, RW1, RW2, and RW3 into the FIFO queue so that there's no 
#     space left. it also reads HM0 into UB0.
# instrs multiply UB0 with the fifo queue into ACC0. Then halt.
def mmc_hlt_full_yes_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RW 0", "RW 1", "RW 2", "RW 3", "RHM 0 0 1"],
                       instrs=[f"MMC.S 0 0 {L1}", "HLT"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_hlt_full_yes_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)



### ACT-RHM TESTS ###
def test_all_act_rhm(test_function, bitwidths, matsizes):
    return {
        "act_rhm_same_ub": test_function(act_rhm_same_ub, bitwidths, matsizes),
        "act_rhm_diff_ub": test_function(act_rhm_diff_ub, bitwidths, matsizes),
    }

# accumulate from ACC0 to UB0, move from HM0 to UB0 (same UB)
# setup reads HM1 into UB1, loads RW0, and multiplies UB1 with RW0 (no S) into 
#     ACC0 to prepare for instr 1 to write it back to UB.
# instrs write ACC0 to UB0 and write from HM0 to UB0.
def act_rhm_same_ub(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 1 1 1", "RW 0", "MMC 0 1 1"],
                       instrs=[f"ACT 0 0 {L1}", f"RHM 0 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="act_rhm_same_ub",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# accumulate from ACC0 to UB0, move from HM0 to UB1 (different UB)
# setup reads HM2 into UB2, loads RW0, and multiplies UB2 with RW0 (no S) into 
#     ACC0 to prepare for instr 1 to write it back to UB.
# instrs write ACC0 to UB0 and write from HM0 to UB1.
def act_rhm_diff_ub(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 2 2 1", "RW 0", "MMC 0 2 1"],
                       instrs=[f"ACT 0 0 {L1}", f"RHM 0 1 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="act_rhm_diff_ub",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)



### ACT-WHM TESTS ###
def test_all_act_whm(test_function, bitwidths, matsizes):
    return {
        "act_whm_same_ub": test_function(act_whm_same_ub, bitwidths, matsizes),
        "act_whm_diff_ub": test_function(act_whm_diff_ub, bitwidths, matsizes),
    }

# accumulate from ACC0 to UB0, move from UB0 to HM0 (same UB)
# setup reads HM1 into UB1, loads RW0, and multiplies UB1 with RW0 (no S) into
#     ACC0 to prepare for instr 1 to write it back to UB.
# instrs write ACC0 to UB0 and write from UB0 to HM0.
def act_whm_same_ub(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 1 1 1", "RW 0", "MMC 0 1 1"],
                       instrs=[f"ACT 0 0 {L1}", f"WHM 0 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="act_whm_same_ub",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# accumulate from ACC0 to UB0, move from UB1 to HM0 (different UB)
# setup reads HM1 into HM1, loads HM2 into HM2, loads RW0, and multiplies HM2
#     with RW0 (no S) into ACC0 to prepare for instr 1 to write it back to UB.
# instrs write ACC0 to UB0 and write from UB1 to HM0.
def act_whm_diff_ub(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 1 1 1", "RHM 2 2 1", "RW 0", "MMC 0 2 1"],
                       instrs=[f"ACT 0 0 {L1}", f"WHM 0 1 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="act_whm_diff_ub",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)



### ACT-RW TESTS ###
def test_all_act_rw(test_function, bitwidths, matsizes):
    return {
        "act_rw": test_function(act_rw, bitwidths, matsizes),
    }

# accumulate from ACC0 to UB0, read from RW0
# setup reads HM1 into UB1, loads RW0, and multiplies UB1 with RW0 (no S) into
#     ACC0 to prepare for instr 1 to write it back to UB.
# instrs write ACC0 to UB0 and load RW1 into the weight queue.
def act_rw(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 1 1 1", "RW 0", "MMC 0 1 1"],
                       instrs=[f"ACT 0 0 {L1}", "RW 1"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="act_rw",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)



### ACT-MMC TESTS ###
def test_all_act_mmc(test_function, bitwidths, matsizes):
    return {
        "act_mmc_diff_ub_diff_acc_no_s": test_function(act_mmc_diff_ub_diff_acc_no_s, bitwidths, matsizes),
        "act_mmc_diff_ub_diff_acc_yes_s": test_function(act_mmc_diff_ub_diff_acc_yes_s, bitwidths, matsizes),
        "act_mmc_same_ub_diff_acc_no_s": test_function(act_mmc_same_ub_diff_acc_no_s, bitwidths, matsizes),
        "act_mmc_same_ub_diff_acc_yes_s": test_function(act_mmc_same_ub_diff_acc_yes_s, bitwidths, matsizes),
        "act_mmc_diff_ub_same_acc_no_s": test_function(act_mmc_diff_ub_same_acc_no_s, bitwidths, matsizes),
        "act_mmc_diff_ub_same_acc_yes_s": test_function(act_mmc_diff_ub_same_acc_yes_s, bitwidths, matsizes),
        "act_mmc_same_ub_same_acc_no_s": test_function(act_mmc_same_ub_same_acc_no_s, bitwidths, matsizes),
        "act_mmc_same_ub_same_acc_yes_s": test_function(act_mmc_same_ub_same_acc_yes_s, bitwidths, matsizes),
    }

# accumulate from ACC0 to UB0, multiplying UB1 into ACC1 no .S (different ACC and UB)
# setup reads HM0 into UB0, reads HM1 into UB1, loads RW0 and RW1, and 
#     multiplies UB0 with RW0 (no S) into ACC0 to prepare for instr 1 to write 
#     ACC0 back to UB.
# instrs write ACC0 to UB0 and multiply UB1 with RW0 (no S) into ACC1.
def act_mmc_diff_ub_diff_acc_no_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1", "RHM 1 1 1", "RW 0", "RW 1", 
                              "MMC 0 0 1"],
                       instrs=[f"ACT 0 0 {L1}", f"MMC 1 1 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="act_mmc_diff_ub_diff_acc_no_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# accumulate from ACC0 to UB0, multiplying UB1 into ACC1 w/ .S (different ACC and UB)
# setup reads HM0 into UB0, reads HM1 into UB1, loads RW0 and RW1, and
#     multiplies UB0 with RW0 (no S) into ACC0 to prepare for instr 1 to write
#     ACC0 back to UB.
# instrs write ACC0 to UB0 and multiply UB1 with RW0 (w/ S) into ACC1.
def act_mmc_diff_ub_diff_acc_yes_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1", "RHM 1 1 1", "RW 0", "RW 1", 
                              "MMC 0 0 1"],
                       instrs=[f"ACT 0 0 {L1}", f"MMC.S 1 1 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="act_mmc_diff_ub_diff_acc_yes_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# accumulate from ACC0 to UB0, multiplying UB0 into ACC1 no .S (same UB)
# setup reads HM0 into UB0, loads RW0 and RW1, and multiplies UB0 with RW0
#     (no S) into ACC0 to prepare for instr 1 to write ACC0 back to UB.
# instrs write ACC0 to UB0 and multiply UB0 with RW0 (no S) into ACC1.
def act_mmc_same_ub_diff_acc_no_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1", "RW 0", "RW 1", "MMC 0 0 1"],
                       instrs=[f"ACT 0 0 {L1}", f"MMC 1 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="act_mmc_same_ub_diff_acc_no_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# accumulate from ACC0 to UB0, multiplying UB0 into ACC1 w/ .S (same UB)
# setup reads HM0 into UB0, loads RW0 and RW1, and multiplies UB0 with RW0
#     (no S) into ACC0 to prepare for instr 1 to write ACC0 back to UB.
# instrs write ACC0 to UB0 and multiply UB0 with RW0 (w/ S) into ACC1.
def act_mmc_same_ub_diff_acc_yes_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1", "RW 0", "RW 1", "MMC 0 0 1"],
                       instrs=[f"ACT 0 0 {L1}", f"MMC.S 1 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="act_mmc_same_ub_diff_acc_yes_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# accumulate from ACC0 to UB0, multiplying UB1 into ACC0 no .S (same ACC)
# setup reads HM0 into UB0, reads HM1 into UB1, loads RW0 and RW1, and 
#     multiplies UB0 with RW0 (no S) into ACC0 to prepare for instr 1 to write
#     ACC0 back to UB.
# instrs write ACC0 to UB0 and multiply UB1 with RW0 (no S) into ACC0.
def act_mmc_diff_ub_same_acc_no_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1", "RHM 1 1 1", "RW 0", "RW 1", 
                              "MMC 0 0 1"],
                       instrs=[f"ACT 0 0 {L1}", f"MMC 0 1 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="act_mmc_diff_ub_same_acc_no_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# accumulate from ACC0 to UB0, multiplying UB1 into ACC0 w/ .S (same ACC)
# setup reads HM0 into UB0, reads HM1 into UB1, loads RW0 and RW1, and
#     multiplies UB0 with RW0 (no S) into ACC0 to prepare for instr 1 to write
#     ACC0 back to UB.
# instrs write ACC0 to UB0 and multiply UB1 with RW0 (w/ S) into ACC0.
def act_mmc_diff_ub_same_acc_yes_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1", "RHM 1 1 1", "RW 0", "RW 1", 
                              "MMC 0 0 1"],
                       instrs=[f"ACT 0 0 {L1}", f"MMC.S 0 1 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="act_mmc_diff_ub_same_acc_yes_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# accumulate from ACC0 to UB0, multiplying UB0 into ACC0 no .S (same ACC and UB)
# setup reads HM0 into UB0, loads RW0 and RW1, and multiplies UB0 with RW0 
#     (no S) into ACC0 to prepare for instr 1 to write ACC0 back to UB.
# instrs write ACC0 to UB0 and multiply UB0 with RW0 (no S) into ACC0.
def act_mmc_same_ub_same_acc_no_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1", "RW 0", "RW 1", "MMC 0 0 1"],
                       instrs=[f"ACT 0 0 {L1}", f"MMC 0 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="act_mmc_same_ub_same_acc_no_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# accumulate from ACC0 to UB0, multiplying UB0 into ACC0 w/ .S (same ACC and UB)
# setup reads HM0 into UB0, loads RW0 and RW1, and multiplies UB0 with RW0
#     (no S) into ACC0 to prepare for instr 1 to write ACC0 back to UB.
# instrs write ACC0 to UB0 and multiply UB0 with RW0 (w/ S) into ACC0.
def act_mmc_same_ub_same_acc_yes_s(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1", "RW 0", "RW 1", "MMC 0 0 1"],
                       instrs=[f"ACT 0 0 {L1}", f"MMC.S 0 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="act_mmc_same_ub_same_acc_yes_s",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)



### ACT-ACT TESTS ###
def test_all_act_act(test_function, bitwidths, matsizes):
    return {
        "act_act_diff_ub_diff_acc": test_function(act_act_diff_ub_diff_acc, bitwidths, matsizes),
        "act_act_same_ub_diff_acc": test_function(act_act_same_ub_diff_acc, bitwidths, matsizes),
        "act_act_diff_ub_same_acc": test_function(act_act_diff_ub_same_acc, bitwidths, matsizes),
        "act_act_same_ub_same_acc": test_function(act_act_same_ub_same_acc, bitwidths, matsizes),
    }

# accumulate from ACC0 to UB0, accumulate from ACC1 to UB1 (different UB and ACC)
# setup reads HM0 into UB0, reads HM1 into UB1, loads RW0, multiplies UB0 with
#     RW0 (no S) into ACC0, and multiplies UB1 with RW0 (no S) into ACC1.
# instrs write ACC0 to UB0 and write ACC1 to UB1.
def act_act_diff_ub_diff_acc(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1", "RHM 1 1 1", "RW 0", "MMC 0 0 1",
                              "MMC 1 1 1"],
                       instrs=[f"ACT 0 0 {L1}", f"ACT 1 1 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="act_act_diff_ub_diff_acc",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# accumulate from ACC0 to UB0, accumulate from ACC1 to UB0 (same UB)
# setup reads HM0 into UB0, reads HM1 into UB1, loads RW0, multiplies UB0 with
#     RW0 (no S) into ACC0, and multiplies UB1 with RW0 (no S) into ACC1.
# instrs write ACC0 and ACC1 to UB0.
def act_act_same_ub_diff_acc(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1", "RHM 1 1 1", "RW 0", "MMC 0 0 1",
                              "MMC 1 1 1"],
                       instrs=[f"ACT 0 0 {L1}", f"ACT 1 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="act_act_same_ub_diff_acc",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# accumulate from ACC0 to UB0, accumulate from ACC0 to UB1 (same ACC)
# setup reads HM0 into UB0, loads RW0, and multiples UB0 with RW0 (no S) into
#     ACC0.
# instrs write ACC0 to UB0 and UB1.
def act_act_diff_ub_same_acc(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1", "RW 0", "MMC 0 0 1"],
                       instrs=[f"ACT 0 0 {L1}", f"ACT 0 1 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="act_act_diff_ub_same_acc",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)

# accumulate from ACC0 to UB0, accumulate from ACC0 to UB0 (same UB and ACC)
# setup reads HM0 into UB0, loads RW0, and multiples UB0 with RW0 (no S) into
#     ACC0.
# instrs both write ACC0 to UB0.
def act_act_same_ub_same_acc(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 0 0 1", "RW 0", "MMC 0 0 1"],
                       instrs=[f"ACT 0 0 {L1}", f"ACT 0 0 {L2}"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="act_act_same_ub_same_acc",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)



### ACT-HLT TESTS ###
def test_all_act_hlt(test_function, bitwidths, matsizes):
    return {
        "act_hlt": test_function(act_hlt, bitwidths, matsizes),
    }

# accumulate from ACC0 to UB0, halt
# setup reads HM1 into UB1, loads RW0, and multiplies UB1 with RW0 (no S) into
#     ACC0 to prepare for instr 1 to write it back to UB.
# instrs write ACC0 to UB0 and halt.
def act_hlt(distance, bitwidth, matsize, use_nops):
    return squish_test(setup=["RHM 1 1 1", "RW 0", "MMC 0 1 1"],
                       instrs=[f"ACT 0 0 {L1}", "HLT"], cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="act_hlt",
                       reset=False, absoluteaddrs=False, test_folder=TEST_FOLDER,
                       ctrl_distance = START_DISTANCE, use_nops=use_nops)



def test_all(test_func, bitwidths, matsizes):
    tests = {}

    tests.update(test_all_rhm_rhm(test_func, bitwidths, matsizes))
    tests.update(test_all_rhm_whm(test_func, bitwidths, matsizes))
    tests.update(test_all_rhm_rw(test_func, bitwidths, matsizes))
    tests.update(test_all_rhm_mmc(test_func, bitwidths, matsizes))
    tests.update(test_all_rhm_act(test_func, bitwidths, matsizes))
    tests.update(test_all_rhm_hlt(test_func, bitwidths, matsizes))

    tests.update(test_all_whm_rhm(test_func, bitwidths, matsizes))
    tests.update(test_all_whm_whm(test_func, bitwidths, matsizes))
    tests.update(test_all_whm_rw(test_func, bitwidths, matsizes))
    tests.update(test_all_whm_mmc(test_func, bitwidths, matsizes))
    tests.update(test_all_whm_act(test_func, bitwidths, matsizes))
    tests.update(test_all_whm_hlt(test_func, bitwidths, matsizes))

    tests.update(test_all_rw_rhm(test_func, bitwidths, matsizes))
    tests.update(test_all_rw_whm(test_func, bitwidths, matsizes))
    tests.update(test_all_rw_rw(test_func, bitwidths, matsizes))
    tests.update(test_all_rw_mmc(test_func, bitwidths, matsizes))
    tests.update(test_all_rw_act(test_func, bitwidths, matsizes))
    tests.update(test_all_rw_hlt(test_func, bitwidths, matsizes))

    tests.update(test_all_mmc_rhm(test_func, bitwidths, matsizes))
    tests.update(test_all_mmc_whm(test_func, bitwidths, matsizes))
    tests.update(test_all_mmc_rw(test_func, bitwidths, matsizes))
    tests.update(test_all_mmc_mmc(test_func, bitwidths, matsizes))
    tests.update(test_all_mmc_act(test_func, bitwidths, matsizes))
    tests.update(test_all_mmc_hlt(test_func, bitwidths, matsizes))

    tests.update(test_all_act_rhm(test_func, bitwidths, matsizes))
    tests.update(test_all_act_whm(test_func, bitwidths, matsizes))
    tests.update(test_all_act_rw(test_func, bitwidths, matsizes))
    tests.update(test_all_act_mmc(test_func, bitwidths, matsizes))
    tests.update(test_all_act_act(test_func, bitwidths, matsizes))
    tests.update(test_all_act_hlt(test_func, bitwidths, matsizes))

    return tests

def dtest_all(bitwidths, matsizes):
    return test_all(min_viable_distance_all, bitwidths, matsizes)

def ntest_all(bitwidths, matsizes):
    return test_all(no_nop_comparison_all, bitwidths, matsizes)
