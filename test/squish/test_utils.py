# utilities for running squish tests
from squishtest import squish_test



# run a squish test with chosen bitwidth and matsize for different distances. 
# start from a chosen large distance and reduce until the test doesn't match the
# control, or a distance of 1 is reached successfully.
# return the lowest distance that was successful.
def min_viable_distance_fixed(function, bitwidth, matsize, start_distance=50):
    distance = start_distance
    while distance > 0:
        result, _ = function(distance, bitwidth, matsize)
        if not result:
            break
        distance -= 1
    return distance + 1
    
# find the mimimum viable distance for a variety of bitwidths and matsizes.
# return a nested dictionary that holds the minimum viable distance for each
# combination of bitwidth and matsize. accessed as dist = d[bitwidth][matsize].
def min_viable_distance_all(function, bitwidths, matsizes):
    d = {}
    for bitwidth in bitwidths:
        d[bitwidth] = {}
        for matsize in matsizes:
            distance = min_viable_distance_fixed(function, bitwidth, matsize)
            d[bitwidth][matsize] = distance
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
def test_mmc_switch_behavior(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 0 0 1", "RHM 1 1 1", "RHM 2 2 1",
                              "RW 0", "RW 1",
                              "MMC 0 0 1", "MMC.S 1 1 1", "MMC.S 2 2 1",
                              "ACT 0 3 1", "ACT 1 4 1", "ACT 2 5 1",
                              "WHM 3 3 1", "WHM 4 4 1", "WHM 5 5 1"],
                       instrs=["NOP", "NOP"],
                       cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="test_mmc_switch_behavior",
                       reset=True, absoluteaddrs=False)



### RHM-RHM TESTS ###
def run_all_rhm_rhm(bitwidths, matsizes):
    pass

# from HM0 to UB0 and from HM1 to UB1 (no overlap in HM or UB)
# setup reads the wrong matrices to slots 0 and 1 to start with. that way, the
#     test confirms that RHM overwrites existing data correctly.
# instrs write the correct matrices to slots 0 and 1.
# cleanup writes the content of the UB back to different slots in the HM. that
#     way, the test confirms that the right data was actually written to the UB.
def rhm_rhm_no_overlap(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 2 0 1", "RHM 3 1 1"],
                       instrs=["RHM 0 0 1", "RHM 1 1 1"],
                       cleanup=["WHM 2 0 1", "WHM 3 1 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rhm_rhm_no_overlap", 
                       reset=True, absoluteaddrs=False)

# from HM0 to UB0 and from HM1 to UB0 (same destination in UB)
# setup is not needed to test that data is overwritten correctly.
# instrs write HM 0 to UB 0 and then overwrite UB 0 with HM 1.
# cleanup writes the content of UB 0 back to a new slot in the HM (slot 2).
def rhm_rhm_same_ub(distance, bitwidth, matsize):
    return squish_test(setup=[],
                       instrs=["RHM 0 0 1", "RHM 1 0 1"],
                       cleanup=["WHM 2 0 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rhm_rhm_same_ub", 
                       reset=True, absoluteaddrs=False)

# from HM0 to UB0 and from HM0 to UB1 (same origin in HM)
# setup is not needed to test that data is written to two different places
#     correctly.
# instrs write HM 0 to UB 0 and write HM 0 again to UB 1.
# cleanup writes the content of UB 0 and UB 1 back to new slots in the HM.
def rhm_rhm_same_hm(distance, bitwidth, matsize):
    return squish_test(setup=[],
                       instrs=["RHM 0 0 1", "RHM 0 1 1"],
                       cleanup=["WHM 2 0 1", "WHM 3 1 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rhm_rhm_same_hm", 
                       reset=True, absoluteaddrs=False)

# from HM0 to UB0 and from HM0 to UB0 (same origin in HM and destination in UB)
# setup is not needed to test that data is written to the same place twice.
# instrs write HM 0 to UB 0 and then write HM 0 to UB 0 again.
# cleanup writes the content of UB 0 back to a new slot in the HM (slot 2).
def rhm_rhm_identical(distance, bitwidth, matsize):
    return squish_test(setup=[],
                       instrs=["RHM 0 0 1", "RHM 0 0 1"],
                       cleanup=["WHM 2 0 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rhm_rhm_identical", 
                       reset=True, absoluteaddrs=False)



### RHM-WHM TESTS ###
def run_all_rhm_whm():
    pass

# from HM0 to UB0 and from UB1 to HM1 (no overlap in HM or UB)
# setup preloads something into UB 1 for WHM to read from.
# instrs write HM 0 to UB 0 and then write UB 1 to HM 1.
# cleanup is not needed, since at this point HM2 should already be written to
#     HM1.
def rhm_whm_no_overlap(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 2 1 1"],
                       instrs=["RHM 0 0 1", "WHM 1 1 1"],
                       cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rhm_whm_no_overlap",
                       reset=True, absoluteaddrs=False)

# from HM0 to UB0 and from UB0 to HM1 (same UB)
# setup is not needed to test that the main instructions move data to UB and
#     back to HM in a different slot (1).
# instrs write HM 0 to UB 0 and then write UB 0 to HM 1.
# cleanup is not needed, since at this point HM1 should already be written to
def rhm_whm_same_ub(distance, bitwidth, matsize):
    return squish_test(setup=[],
                       instrs=["RHM 0 0 1", "WHM 1 0 1"],
                       cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rhm_whm_same_ub",
                       reset=True, absoluteaddrs=False)

# from HM0 to UB0 and from UB1 to HM0 (same HM)
# setup writes a differnt matrix (HM2) to UB 1 to ensure that it's written to 
#     HM0.
# instrs write HM 0 to UB 0 and then write UB 1 to HM 0.
# cleanup writes UB 0 back to HM 1 to ensure that the correct data was written.
def rhm_whm_same_hm(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 2 1 1"],
                       instrs=["RHM 0 0 1", "WHM 0 1 1"],
                       cleanup=["WHM 1 0 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rhm_whm_same_hm",
                       reset=True, absoluteaddrs=False)

# from HM0 to UB0 and from UB0 to HM0 (same UB and HM)
# setup writes a different matrix (HM1) to UB 0 to ensure that it's later
#     overwritten.
# instrs write HM 0 to UB 0 and then write UB 0 directly back to HM 0.
# cleanup writes UB 0 back to a third HM slot (HM2) to ensure that the correct
#     data was written to UB 0.
def rhm_whm_identical(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 1 0 1"],
                       instrs=["RHM 0 0 1", "WHM 0 0 1"],
                       cleanup=["WHM 2 0 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rhm_whm_identical",
                       reset=True, absoluteaddrs=False)



### RHM-RW TESTS ###
def run_all_rhm_rw():
    pass

# from HM0 to UB0 and reading from RW0
# setup is not needed.
# instrs write HM 0 to UB 0 and then loads a weight into RW 0.
# cleanup needs to test that the weight was loaded correctly, so it does a
#     matrix multiplication with the weight and the matrix in UB 0, writes the
#     product to UB1, and then writes UB1 back to HM 1.
def rhm_rw(distance, bitwidth, matsize):
    return squish_test(setup=[],
                       instrs=["RHM 0 0 1", "RW 0"],
                       cleanup=["MMC 0 0 1", "ACT 0 1 1", "WHM 1 1 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rhm_rw",
                       reset=True, absoluteaddrs=False)



### RHM-MMC TESTS ###
def run_all_rhm_mmc():
    pass

# from HM0 to UB0 and multiplying UB0 with ACC0, no .S (same UB)
# setup reads a weight into RW 0 for use in multiplication.
# instrs write HM0 to UB0 and then multiply UB0 with RW0 into ACC0.
# cleanup writes the result of the multiplication back to UB1 and then HM1.
def rhm_mmc_same_ub_no_s(distance, bitwidth, matsize):
    return squish_test(setup=["RW 0"],
                       instrs=["RHM 0 0 1", "MMC 0 0 1"],
                       cleanup=["ACT 0 1 1", "WHM 1 1 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rhm_mmc_same_ub_no_s",
                       reset=True, absoluteaddrs=False)

# from HM0 to UB0 and multiplying UB1 with ACC0, no .S (different UBs)
# setup reads a weight into RW 0 for use in multiplication and reads a matrix
#     from HM1 to UB1 for use in multiplication.
# instrs write HM0 to UB0 and then multiply UB1 with RW0 into ACC0.
# cleanup writes the result of the multiplication back to UB2 and then HM2, and
#     writes the matrix from UB0 to HM3.
def rhm_mmc_no_overlap_no_s(distance, bitwidth, matsize):
    return squish_test(setup=["RW 0", "RHM 1 1 1"],
                       instrs=["RHM 0 0 1", "MMC 0 1 1"],
                       cleanup=["ACT 0 2 1", "WHM 2 2 1", "WHM 3 0 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rhm_mmc_no_overlap_no_s",
                       reset=True, absoluteaddrs=False)

# from HM0 to UB0 and multiplying UB0 with ACC0, w/ .S (same UB)
# setup reads a weight into RW 0 and RW 1 (to make sure it switches after MMC).
# instrs write HM0 to UB0 and then multiply UB0 with RW0 into ACC0 with .S.
# cleanup writes the multiplication in ACC0 to UB1 and back to HM1, and then
#     has to check that RW1 is switched to. so it writes HM2 to UB2, multiplies
#     UB2 with RW0 (as the new weight should be there now), writes the result to
#     UB3, and then writes UB3 back to HM3.
def rhm_mmc_same_ub_yes_s(distance, bitwidth, matsize):
    return squish_test(setup=["RW 0", "RW 1"],
                       instrs=["RHM 0 0 1", "MMC.S 0 0 1"],
                       cleanup=["ACT 0 1 1", "WHM 1 1 1", "RHM 2 2 1", 
                                "MMC 1 2 1", "WHM 1 3 1", "WHM 3 3 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rhm_mmc_same_ub_s",
                       reset=True, absoluteaddrs=False)

# from HM0 to UB0 and multiplying UB1 with ACC0, w/ .S (different UBs)
# setup reads a weight into RW 0 and RW 1 (to make sure it switches after MMC)
#     and reads a matrix from HM1 to UB1 for use in multiplication.
# instrs write HM0 to UB0 and multiplies UB1 with RW0 into ACC0 with .S.
# cleanup writes the multiplication in ACC0 to UB2 and back to HM2, and then
#     has to check that RW1 is switched to. so it writes HM3 to UB3, multiplies
#     UB3 with RW0 (as the new weight should be there now), writes the result to
#     UB4, and then writes UB4 back to HM4. lastly, it writes the matrix
#     originally written into UB0 into HM5 to make sure it got written.
def rhm_mmc_no_overlap_yes_s(distance, bitwidth, matsize):
    return squish_test(setup=["RW 0", "RW 1", "RHM 1 1 1"],
                       instrs=["RHM 0 0 1", "MMC.S 0 1 1"],
                       cleanup=["ACT 0 2 1", "WHM 2 2 1", "RHM 3 3 1", 
                                "MMC 1 3 1", "WHM 1 4 1", "WHM 4 4 1",
                                "WHM 5 0 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rhm_mmc_no_overlap_s",
                       reset=True, absoluteaddrs=False)



### RHM-ACT TESTS ###
def run_all_rhm_act():
    pass

# from HM0 to UB0 and accumulate from ACC0 to UB0 (same UB)
# setup reads HM1 into UB1 and reads RW0 into the weight queue, and multiplies
#     them into ACC0.
# instrs write HM0 to UB0 and then accumulate from ACC0 to UB0, overwriting the
#     existing data.
# cleanup writes the overwritten UB0 into HM2.
def rhm_act_same_ub(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 1 1 1", "RW 0", "MMC 0 1 1"],
                       instrs=["RHM 0 0 1", "ACT 0 0 1"],
                       cleanup=["WHM 2 0 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rhm_act_same_ub",
                       reset=True, absoluteaddrs=False)

# from HM0 to UB0 and accumulate from ACC0 to UB1 (different UBs)
# setup reads HM1 into UB1, reads RW0 into the weight queue, and multiplies
#     them into ACC0.
# instrs write HM0 to UB0 and then accumulate from ACC0 to UB1.
# cleanup writes UB0 into HM2 and writes the accumulated UB1 into HM3.
def rhm_act_no_overlap(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 1 1 1", "RW 0", "MMC 0 1 1"],
                       instrs=["RHM 0 0 1", "ACT 0 1 1"],
                       cleanup=["WHM 2 0 1", "WHM 3 1 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rhm_act_no_overlap",
                       reset=True, absoluteaddrs=False)



### WHM-RHM TESTS ###
def run_all_whm_rhm():
    pass

# from UB0 to HM0 and from HM1 to UB1 (no overlap in HM or UB)
# setup writes a matrix from HM2 to UB0
# instrs write from UB0 to HM0 and from HM1 to UB1
# cleanup writes UB1 to HM3
def whm_rhm_no_overlap(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 2 0 1"],
                       instrs=["WHM 0 0 1", "RHM 1 1 1"],
                       cleanup=["WHM 3 1 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="whm_rhm_no_overlap",
                       reset=True, absoluteaddrs=False)

# from UB0 to HM0 and from HM1 to UB0 (same UB)
# setup writes a matrix from HM2 to UB0 so that it has content to start with
# instrs write from UB0 to HM0 and from HM1 to UB0
# cleanup writes UB0 to HM3 so we can see the overwritten data
def whm_rhm_same_ub(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 2 0 1"],
                       instrs=["WHM 0 0 1", "RHM 1 0 1"],
                       cleanup=["WHM 3 0 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="whm_rhm_same_ub",
                       reset=True, absoluteaddrs=False)

# from UB0 to HM0 and from HM0 to UB1 (same HM)
# setup writes a matrix from HM1 to UB1 so that it has content to start with
# instrs write from UB0 to HM0 and from HM0 to UB1
# cleanup writes UB1 to HM2 so we can see the overwritten data
def whm_rhm_same_hm(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 1 0 1"],
                       instrs=["WHM 0 0 1", "RHM 0 1 1"],
                       cleanup=["WHM 2 1 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="whm_rhm_same_hm",
                       reset=True, absoluteaddrs=False)

# from UB0 to HM0 and from HM0 to UB0 (same UB and HM)
# setup writes a matrix from HM1 to UB0 so that it has content to start with
# instrs write from UB0 to HM0 and from HM0 to UB0
# cleanup writes UB0 to HM2 so we can see the overwritten data
def whm_rhm_identical(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 1 0 1"],
                       instrs=["WHM 0 0 1", "RHM 0 0 1"],
                       cleanup=["WHM 2 0 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="whm_rhm_identical",
                       reset=True, absoluteaddrs=False)



### WHM-WHM TESTS ###
def run_all_whm_whm():
    pass

# from UB0 to HM0 and from UB1 to HM1 (no overlap in HM or UB)
# setup writes matrices from HM2 to UB0 and from HM3 to UB1 to get different 
#     values in them.
# instrs write from UB0 to HM0 and from UB1 to HM1
# cleanup is not needed
def whm_whm_no_overlap(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 2 0 1", "RHM 3 1 1"],
                       instrs=["WHM 0 0 1", "WHM 1 1 1"],
                       cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="whm_whm_no_overlap",
                       reset=True, absoluteaddrs=False)

# from UB0 to HM0 and from UB1 to HM0 (same destination in HM)
# setup writes matrices from HM1 to UB0 and from HM2 to UB1 to get different
#     values in them.
# instrs write from UB0 to HM0 and then write from UB1 to HM0
# cleanup is not needed
def whm_whm_same_hm(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 1 0 1", "RHM 2 1 1"],
                       instrs=["WHM 0 0 1", "WHM 0 1 1"],
                       cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="whm_whm_same_hm",
                       reset=True, absoluteaddrs=False)

# from UB0 to HM0 and from UB0 to HM1 (same origin in UB)
# setup writes a matrix from HM2 to UB0 to gett different values in it.
# instrs write from UB0 to HM0 and HM1.
# cleanup is not needed
def whm_whm_same_ub(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 2 0 1"],
                       instrs=["WHM 0 0 1", "WHM 1 0 1"],
                       cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="whm_whm_same_ub",
                       reset=True, absoluteaddrs=False)

# from UB0 to HM0 and from UB0 to HM0 (same origin in UB and destination in HM)
# setup writes a matrix from HM1 to UB0 to get different values in it.
# instrs write from UB0 to HM0 and then write from UB0 to HM0 again
# cleanup is not needed
def whm_whm_identical(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 1 0 1"],
                       instrs=["WHM 0 0 1", "WHM 0 0 1"],
                       cleanup=[],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="whm_whm_identical",
                       reset=True, absoluteaddrs=False)


### WHM-RW TESTS ###
def run_all_whm_rw():
    pass

# from UB0 to HM0 and reading from RW0
# setup writes a matrix from HM1 to UB0 to put a value in it and prepares for
#     matmul by loading HM2 into UB1. 
# instrs write from UB0 to HM0 and then load a weight into RW0.
# cleanup multiplies the matrix in UB1 with the weight in RW0, writes the result
#     to ACC0, writes ACC0 to UB2, and then writes UB2 to HM3.
def whm_rw(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 1 0 1", "RHM 2 1 1"],
                       instrs=["WHM 0 0 1", "RW 0"],
                       cleanup=["MMC 0 1 1", "ACT 0 2 1", "WHM 3 2 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="whm_rw",
                       reset=True, absoluteaddrs=False)



### WHM-MMC TESTS ###
def run_all_whm_mmc():
    pass

# from UB0 to HM0 and multiplying UB0 into ACC0, no .S (same UB)
# setup loads HM1 into UB0 so that it has a value, and loads RW0 and RW1 into
#     the weight queue.
# instrs write from UB0 to HM0 and then multiply UB0 into ACC0.
# cleanup first writes the result of the multiplication to UB1 and then HM2.
#     then it does another matmul which confirms that the weight queue isn't 
#     switched. this involves reading HM3 into UB2, multiplying UB2 with RW0
#     into ACC1, writing ACC1 to UB3, and then writing UB3 to HM4.
def whm_mmc_same_ub_no_s(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 1 0 1", "RW 0", "RW 1"],
                       instrs=["WHM 0 0 1", "MMC 0 0 1"],
                       cleanup=["ACT 0 1 1", "WHM 2 1 1", "RHM 3 2 1", 
                                "MMC 1 2 1", "ACT 1 3 1", "WHM 4 3 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="whm_mmc_same_ub_no_s",
                       reset=True, absoluteaddrs=False)

# from UB0 to HM0 and multiplying UB1 into ACC0, no .S (different UBs)
# setup loads HM1 into UB1 so that it has a value, and loads RW0 and RW1 into
#     the weight queue.
# instrs write from UB0 to HM0 and then multiply UB1 into ACC0.
# cleanup first writes the result of the multiplication to UB2 and then HM3.
#     then it does another matmul which confirms that the weight queue isn't
#     switched. this involves reading HM4 into UB3, multiplying UB3 with RW0
#     into ACC1, writing ACC1 to UB4, and then writing UB4 to HM5.
def whm_mmc_no_overlap_no_s(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 1 1 1", "RW 0", "RW 1"],
                       instrs=["WHM 0 0 1", "MMC 0 1 1"],
                       cleanup=["ACT 0 2 1", "WHM 3 2 1", "RHM 4 3 1", 
                                "MMC 1 3 1", "ACT 1 4 1", "WHM 5 4 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="whm_mmc_no_overlap_no_s",
                       reset=True, absoluteaddrs=False)

# from UB0 to HM0 and multiplying UB0 into ACC0, w/ .S (same UB)
# setup loads HM1 into UB0 so that it has a value, and loads RW0 and RW1 into
#     the weight queue.
# instrs write from UB0 to HM0 and then multiply UB0 into ACC0.
# cleanup first writes the result of the multiplication to UB1 and then HM2.
#     then it does another matmul which confirms that the weight queue isn't 
#     switched. this involves reading HM3 into UB2, multiplying UB2 with RW1
#     into ACC1, writing ACC1 to UB3, and then writing UB3 to HM4.
def whm_mmc_same_ub_yes_s(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 1 0 1", "RW 0", "RW 1"],
                       instrs=["WHM 0 0 1", "MMC.S 0 0 1"],
                       cleanup=["ACT 0 1 1", "WHM 2 1 1", "RHM 3 2 1", 
                                "MMC 1 2 1", "ACT 1 3 1", "WHM 4 3 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="whm_mmc_same_ub_no_s",
                       reset=True, absoluteaddrs=False)

# from UB0 to HM0 and multiplying UB1 into ACC0, w/ .S (different UBs)
# setup loads HM1 into UB1 so that it has a value, and loads RW0 and RW1 into
#     the weight queue.
# instrs write from UB0 to HM0 and then multiply UB1 into ACC0.
# cleanup first writes the result of the multiplication to UB2 and then HM3.
#     then it does another matmul which confirms that the weight queue isn't
#     switched. this involves reading HM4 into UB3, multiplying UB3 with RW0
#     into ACC1, writing ACC1 to UB4, and then writing UB4 to HM5.
def whm_mmc_no_overlap_no_s(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 1 1 1", "RW 0", "RW 1"],
                       instrs=["WHM 0 0 1", "MMC.S 0 1 1"],
                       cleanup=["ACT 0 2 1", "WHM 3 2 1", "RHM 4 3 1", 
                                "MMC 1 3 1", "ACT 1 4 1", "WHM 5 4 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="whm_mmc_no_overlap_no_s",
                       reset=True, absoluteaddrs=False)



### WHM-ACT TESTS ###
def run_all_whm_act():
    pass

# from UB0 to HM0 and accumulate from ACC0 to UB0 (same UB)
# setup loads HM1 into UB1 so that it has a value, loads RW0 into the weight
#     matrix, and performs the multiplication into ACC0.
# instrs write from UB0 to HM0 and then accumulate from ACC0 to UB0.
# cleanup writes the accumulated UB0 to HM2.
def whm_act_same_ub(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 1 1 1", "RW 0", "MMC 0 1 1"],
                       instrs=["WHM 0 0 1", "ACT 0 0 1"],
                       cleanup=["WHM 2 0 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="whm_act_same_ub",
                       reset=True, absoluteaddrs=False)

# from UB0 to HM0 and accumulate from ACC0 to UB1 (different UBs)
# setup loads HM3 into UB0 so that it has a value, loads HM2 into UB2, loads
#     RW0 into the weight queue, and multiplies UB2 with RW0 into ACC0.
# instrs write from UB0 to HM0 and then accumulate from ACC0 to UB1.
# cleanup writes the accumulated UB1 to HM1.
def whm_act_no_overlap(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 3 0 1", "RHM 2 2 1", "RW 0", "MMC 0 2 1"],
                       instrs=["WHM 0 0 1", "ACT 0 1 1"],
                       cleanup=["WHM 1 1 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="whm_act_no_overlap",
                       reset=True, absoluteaddrs=False)



### RW-RHM TESTS ###
def run_all_rw_rhm():
    pass

# reading from RW0 and moving from HM0 to UB0
# setup not needed.
# instrs load a weight into RW0 and then move a matrix from HM0 to UB0
# cleanup loads a matrix from UB0 to HM1 so it can be read. it also does a 
#     matmul to confirm that the weight was loaded correctly. this involves
#     loading HM2 into UB1, multiplying UB1 with RW0 into ACC0, writing ACC0 to
#     UB2, and then writing UB2 to HM3.
def rw_rhm(distance, bitwidth, matsize):
    return squish_test(setup=[],
                       instrs=["RW 0", "RHM 0 0 1"],
                       cleanup=["WHM 1 0 1", "RHM 2 1 1", "MMC 0 1 1", 
                                "ACT 0 2 1", "WHM 3 2 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rw_rhm",
                       reset=True, absoluteaddrs=False)



### RW-WHM TESTS ###
def run_all_rw_whm():
    pass

# reading from RW0 and moving from UB0 to HM0
# setup loads a matrix from HM1 into UB0 so that it has a value.
# instrs load a weight into RW0 and then move a matrix from UB0 to HM0.
# cleanup needs to perform a matmul to show that the weight was loaded 
#     correctly. this involves loading HM2 into UB1, multiplying UB1 with RW0
#     into ACC0, writing ACC0 to UB2, and then writing UB2 to HM3.
def rw_whm(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 1 0 1"],
                       instrs=["RW 0", "WHM 0 0 1"],
                       cleanup=["RHM 2 1 1", "MMC 0 1 1", "ACT 0 2 1", 
                                "WHM 3 2 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rw_whm",
                       reset=True, absoluteaddrs=False)



### RW-RW TESTS ###
def run_all_rw_rw():
    pass

# reading from RW0 and RW0, buffer starts empty (same weights)
# setup not needed.
# instrs load RW0 into the weight queue and then load RW0 again.
# cleanup needs to confirm that the weights were loaded correctly. so it loads 
#     matrices from HM0 and HM1 into UB0 and UB1, multiplies UB0 with the first 
#     RW0 into ACC0, multiplies UB1 with the second RW0 into ACC1, writes ACC0
#     to UB2, writes ACC1 to UB3, and lastly writes UB2 and UB3 to HM2 and HM3.
def rw_rw_same_weights_empty(distance, bitwidth, matsize):
    return squish_test(setup=[],
                       instrs=["RW 0", "RW 0"],
                       cleanup=["RHM 0 0 1", "RHM 1 1 1", 
                                "MMC.S 0 0 1", "MMC.S 1 1 1", 
                                "ACT 0 2 1", "ACT 1 3 1", 
                                "WHM 2 2 1", "WHM 3 3 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rw_rw_same_weights_empty",
                       reset=True, absoluteaddrs=False)

# reading from RW0 and RW1, buffer starts empty (different weights)
# setup not needed.
# instrs load RW0 into the weight queue and then load RW1.
# cleanup needs to confirm that the weights were loaded correctly. so it loads 
#     matrices from HM0 and HM1 into UB0 and UB1, multiplies UB0 with the first 
#     RW0 into ACC0, multiplies UB1 with the second RW0 into ACC1, writes ACC0
#     to UB2, writes ACC1 to UB3, and lastly writes UB2 and UB3 to HM2 and HM3.
def rw_rw_diff_weights_empty(distance, bitwidth, matsize):
    return squish_test(setup=[],
                       instrs=["RW 0", "RW 1"],
                       cleanup=["RHM 0 0 1", "RHM 1 1 1", 
                                "MMC.S 0 0 1", "MMC.S 1 1 1", 
                                "ACT 0 2 1", "ACT 1 3 1", 
                                "WHM 2 2 1", "WHM 3 3 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rw_rw_same_weights_empty",
                       reset=True, absoluteaddrs=False)

# reading from RW0 and RW0, buffer starts with one space (same weights)
# setup reads RW0, RW1, and RW2 into the weight queue so that there's one slot
#     remaining.
# instrs load RW3 into the weight queue and then load RW3 again.
# cleanup needs to confirm that the weights were loaded correctly. it does four
#     matmuls, one for each slot in the weight queue, which should be full after
#     the instrs. load 4 matrices from HM to UB, multiply them into ACC, write
#     them back to UB, and then write them to HM.
def rw_rw_same_weights_one_space(distance, bitwidth, matsize):
    return squish_test(setup=["RW 0", "RW 1", "RW 2"],
                       instrs=["RW 3", "RW 3"],
                       cleanup=["RHM 0 0 1", "RHM 1 1 1", "RHM 2 2 1", 
                                "RHM 3 3 1", 
                                "MMC.S 0 0 1", "MMC.S 1 1 1", "MMC.S 2 2 1", 
                                "MMC.S 3 3 1", 
                                "ACT 0 4 1", "ACT 1 5 1", "ACT 2 6 1", 
                                "ACT 3 7 1", 
                                "WHM 4 4 1", "WHM 5 5 1", "WHM 6 6 1", 
                                "WHM 7 7 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rw_rw_same_weights_one_space",
                       reset=True, absoluteaddrs=False)

# reading from RW0 and RW1, buffer starts with one space (different weights)
# setup reads RW0, RW1, and RW2 into the weight queue so that there's one slot
#     remaining.
# instrs load RW3 into the weight queue and then load RW4.
# cleanup needs to confirm that the weights were loaded correctly. it does four
#     matmuls, one for each slot in the weight queue, which should be full after
#     the instrs. load 4 matrices from HM to UB, multiply them into ACC, write
#     them back to UB, and then write them to HM.
def rw_rw_diff_weights_one_space(distance, bitwidth, matsize):
    return squish_test(setup=["RW 0", "RW 1", "RW 2"],
                       instrs=["RW 3", "RW 4"],
                       cleanup=["RHM 0 0 1", "RHM 1 1 1", "RHM 2 2 1", 
                                "RHM 3 3 1", 
                                "MMC.S 0 0 1", "MMC.S 1 1 1", "MMC.S 2 2 1", 
                                "MMC.S 3 3 1", 
                                "ACT 0 4 1", "ACT 1 5 1", "ACT 2 6 1", 
                                "ACT 3 7 1", 
                                "WHM 4 4 1", "WHM 5 5 1", "WHM 6 6 1", 
                                "WHM 7 7 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rw_rw_diff_weights_one_space",
                       reset=True, absoluteaddrs=False)

# reading from RW0 and RW0, buffer starts full (same weights)
# setup reads RW0, RW1, RW2, and RW3 into the weight queue so that there's one 
#     slot remaining.
# instrs load RW4 into the weight queue and then load RW4 again.
# cleanup needs to confirm that the weights were loaded correctly. it does four
#     matmuls, one for each slot in the weight queue, which should be full after
#     the instrs. load 4 matrices from HM to UB, multiply them into ACC, write
#     them back to UB, and then write them to HM.
def rw_rw_same_weights_full(distance, bitwidth, matsize):
    return squish_test(setup=["RW 0", "RW 1", "RW 2", "RW 3"],
                       instrs=["RW 4", "RW 4"],
                       cleanup=["RHM 0 0 1", "RHM 1 1 1", "RHM 2 2 1", 
                                "RHM 3 3 1", 
                                "MMC.S 0 0 1", "MMC.S 1 1 1", "MMC.S 2 2 1", 
                                "MMC.S 3 3 1", 
                                "ACT 0 4 1", "ACT 1 5 1", "ACT 2 6 1", 
                                "ACT 3 7 1", 
                                "WHM 4 4 1", "WHM 5 5 1", "WHM 6 6 1", 
                                "WHM 7 7 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rw_rw_same_weights_full",
                       reset=True, absoluteaddrs=False)

# reading from RW0 and RW1, buffer starts full (different weights)
# setup reads RW0, RW1, RW2, and RW3 into the weight queue so that there's one 
#     slot remaining.
# instrs load RW4 into the weight queue and then load RW5.
# cleanup needs to confirm that the weights were loaded correctly. it does four
#     matmuls, one for each slot in the weight queue, which should be full after
#     the instrs. load 4 matrices from HM to UB, multiply them into ACC, write
#     them back to UB, and then write them to HM.
def rw_rw_diff_weights_full(distance, bitwidth, matsize):
    return squish_test(setup=["RW 0", "RW 1", "RW 2", "RW 3"],
                       instrs=["RW 4", "RW 5"],
                       cleanup=["RHM 0 0 1", "RHM 1 1 1", "RHM 2 2 1", 
                                "RHM 3 3 1", 
                                "MMC.S 0 0 1", "MMC.S 1 1 1", "MMC.S 2 2 1", 
                                "MMC.S 3 3 1", 
                                "ACT 0 4 1", "ACT 1 5 1", "ACT 2 6 1", 
                                "ACT 3 7 1", 
                                "WHM 4 4 1", "WHM 5 5 1", "WHM 6 6 1", 
                                "WHM 7 7 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rw_rw_diff_weights_full",
                       reset=True, absoluteaddrs=False)



### RW-MMC TESTS ###
def run_all_rw_mmc():
    pass

# reading from RW0, buffer starts empty, multiplying UB0 into ACC0, no .S
# setup reads HM0 into UB0.
# instrs load RW0 into the weight queue and then multiply UB0 and RW0 into ACC0.
# cleanup writes the result of the multiplication to UB1 and then HM1. it also
#     does another matmul to confirm that the weight queue isn't switched. this
#     involves reading HM2 into UB2, reading RW1 into the weight queue, 
#     multiplying UB2 with RW0 into ACC1, writing ACC1 to UB3, and then writing
#     UB3 to HM3.
def rw_mmc_empty_no_s(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 0 0 1"],
                       instrs=["RW 0", "MMC 0 0 1"],
                       cleanup=["ACT 0 1 1", "WHM 1 1 1", 
                                "RHM 2 2 1", "RW 1", "MMC 1 2 1", "ACT 1 3 1", 
                                "WHM 3 3 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rw_mmc_empty_no_s",
                       reset=True, absoluteaddrs=False)

# reading from RW0, buffer starts empty, multiplying UB0 into ACC0, w/ .S
# setup reads HM0 into UB0.
# instrs load RW0 into the weight queue and then multiply UB0 and RW0 into ACC0.
# cleanup writes the result of the multiplication to UB1 and then HM1. it also
#     does another matmul to confirm that the weight queue is switched. this
#     involves reading HM2 into UB2, reading RW1 into the weight queue,
#     multiplying UB2 with RW1 into ACC1, writing ACC1 to UB3, and then writing
#     UB3 to HM3.
def rw_mmc_empty_yes_s(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 0 0 1"],
                       instrs=["RW 0", "MMC.S 0 0 1"],
                       cleanup=["ACT 0 1 1", "WHM 1 1 1", 
                                "RHM 2 2 1", "RW 1", "MMC 1 2 1", "ACT 1 3 1", 
                                "WHM 3 3 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rw_mmc_empty_yes_s",
                       reset=True, absoluteaddrs=False)

# reading from RW0, buffer starts with one space, multiplying UB0 into ACC0, no .S
# setup reads RW0, RW1, and RW2 into the weight queue so that there's one slot
#     remaining. it also reads HM0 into UB0.
# instrs load RW3 into the weight queue and then multiply UB0 and RW0 into ACC0.
# cleanup writes the result of the multiplication from ACC0 to UB1 and then HM1.
#     it also does more matmuls to write the whole weight queue to HM, which 
#     will check that the weight matrix should be RW0, RW1, RW2, RW3 after 
#     instrs.
def rw_mmc_one_space_no_s(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 0 0 1", "RW 0", "RW 1", "RW 2"],
                       instrs=["RW 3", "MMC 0 0 1"],
                       cleanup=["ACT 0 1 1", "WHM 1 1 1", 
                                "RHM 2 2 1", "MMC.S 1 2 1", "ACT 1 3 1", 
                                "WHM 3 3 1",
                                "RHM 4 4 1", "MMC.S 2 4 1", "ACT 2 5 1", 
                                "WHM 5 5 1",
                                "RHM 6 6 1", "MMC.S 3 6 1", "ACT 3 7 1", 
                                "WHM 7 7 1",
                                "RHM 8 8 1", "MMC.S 4 8 1", "ACT 4 9 1", 
                                "WHM 9 9 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rw_mmc_one_space_no_s",
                       reset=True, absoluteaddrs=False)

# reading from RW0, buffer starts with one space, multiplying UB0 into ACC0, w/ .S
# setup reads RW0, RW1, and RW2 into the weight queue so that there's one slot
#     remaining. it also reads HM0 into UB0.
# instrs load RW3 into the weight queue and then multiply UB0 and RW0 into ACC0.
# cleanup writes the result of the multiplication from ACC0 to UB1 and then HM1.
#     it also does more matmuls to write the whole weight queue to HM, which 
#     will check that the weight matrix should be RW1, RW2, RW3 after instrs.
def rw_mmc_one_space_no_s(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 0 0 1", "RW 0", "RW 1", "RW 2"],
                       instrs=["RW 3", "MMC.S 0 0 1"],
                       cleanup=["ACT 0 1 1", "WHM 1 1 1", 
                                "RHM 2 2 1", "MMC.S 1 2 1", "ACT 1 3 1", 
                                "WHM 3 3 1",
                                "RHM 4 4 1", "MMC.S 2 4 1", "ACT 2 5 1", 
                                "WHM 5 5 1",
                                "RHM 6 6 1", "MMC.S 3 6 1", "ACT 3 7 1", 
                                "WHM 7 7 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rw_mmc_one_space_no_s",
                       reset=True, absoluteaddrs=False)

# reading from RW0, buffer starts full, multiplying UB0 into ACC0, no .S
# setup reads RW0, RW1, RW2, and RW3 into the weight queue so that there's no
#     space remaining. it also reads HM0 into UB0.
# instrs load RW4 into the weight queue and then multiply UB0 and RW0 into ACC0.
# cleanup writes the result of the multiplication from ACC0 to UB1 and then HM1.
#     it also does more matmuls to write the whole weight queue to HM, which
#     will check that the weight matrix should be RW0, RW1, RW2, RW3 (or RW4? I'm not actually sure what it does or should do in this position. does it refuse to input after it's full, or does it just replace the 4th slot?)
#     after the instrs under test finish.
def rw_mmc_full_no_s(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 0 0 1", "RW 0", "RW 1", "RW 2", "RW 3"],
                       instrs=["RW 4", "MMC 0 0 1"],
                       cleanup=["ACT 0 1 1", "WHM 1 1 1", 
                                "RHM 2 2 1", "MMC.S 1 2 1", "ACT 1 3 1", 
                                "WHM 3 3 1",
                                "RHM 4 4 1", "MMC.S 2 4 1", "ACT 2 5 1", 
                                "WHM 5 5 1",
                                "RHM 6 6 1", "MMC.S 3 6 1", "ACT 3 7 1", 
                                "WHM 7 7 1",
                                "RHM 8 8 1", "MMC.S 4 8 1", "ACT 4 9 1", 
                                "WHM 9 9 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rw_mmc_full_no_s",
                       reset=True, absoluteaddrs=False)

# reading from RW0, buffer starts full, multiplying UB0 into ACC0, w/ .S
# setup reads RW0, RW1, RW2, and RW3 into the weight queue so that there's no
#     space remaining. it also reads HM0 into UB0.
# instrs load RW4 into the weight queue and then multiply UB0 and RW0 into ACC0.
# cleanup writes the result of the multiplication from ACC0 to UB1 and then HM1.
#     it also does more matmuls to write the whole weight queue to HM, which
#     will check that the weight matrix should be RW1, RW2, RW3 (or RW4? I'm not actually sure what it does or should do in this position. does it refuse to input after it's full, or does it just replace the 4th slot?)
#     after the instrs under test finish.
def rw_mmc_full_no_s(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 0 0 1", "RW 0", "RW 1", "RW 2", "RW 3"],
                       instrs=["RW 4", "MMC 0 0 1"],
                       cleanup=["ACT 0 1 1", "WHM 1 1 1", 
                                "RHM 2 2 1", "MMC.S 1 2 1", "ACT 1 3 1", 
                                "WHM 3 3 1",
                                "RHM 4 4 1", "MMC.S 2 4 1", "ACT 2 5 1", 
                                "WHM 5 5 1",
                                "RHM 6 6 1", "MMC.S 3 6 1", "ACT 3 7 1", 
                                "WHM 7 7 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rw_mmc_full_no_s",
                       reset=True, absoluteaddrs=False)



### RW-ACT TESTS ###
def run_all_rw_act():
    pass

# reading from RW0 and accumulate from ACC0 to UB0
# setup reads HM1 into UB1 so that it has a value, loads RW0, and multiplies
#     them into ACC0 while switching weights. 
# instrs load RW1 into the weight queue and then accumulate from ACC0 to UB0.
# cleanup writes the accumulated UB0 to HM0, and confirms that RW1 loaded
#     correctly. this involves loading HM2 into UB2, multiplying UB2 with RW1
#     into ACC1, writing ACC1 to UB3, and then writing UB3 to HM3.
def rw_act(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 1 1 1", "RW 0", "MMC.S 0 1 1"],
                       instrs=["RW 1", "ACT 0 0 1"],
                       cleanup=["WHM 0 0 1", "RHM 2 2 1", "MMC 1 2 1", 
                                "ACT 1 3 1", "WHM 3 3 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="rw_act",
                       reset=True, absoluteaddrs=False)



### MMC-RHM TESTS ###
def run_all_mmc_rhm():
    pass

# multiplying UB0 into ACC0, no .S, moving from HM0 to UB0 (same UB)
# setup reads HM1 into UB0 so that it has a value, loads RW0, and loads RW1.
# instrs multiply UB0 with RW0 into ACC0 and then move a matrix from HM0 to UB0.
# cleanup writes the result of the multiplication from ACC0 to UB1 and then HM2.
#     it also does another matmul to confirm that the weight queue isn't 
#     switched. this involves reading HM3 into UB2, multiplying UB2 with RW0
#     into ACC1, writing ACC1 to UB3, and then writing UB3 to HM4.
def mmc_rhm_same_ub_no_s(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 1 0 1", "RW 0", "RW 1"],
                       instrs=["MMC 0 0 1", "RHM 0 0 1"],
                       cleanup=["ACT 0 1 1", "WHM 2 1 1", 
                                "RHM 3 2 1", "MMC 1 2 1", "ACT 1 3 1", 
                                "WHM 4 3 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_rhm_same_ub_no_s",
                       reset=True, absoluteaddrs=False)

# multiplying UB0 into ACC0, w/ .S, moving from HM0 to UB0 (same UB)
# setup reads HM1 into UB0 so that it has a value, loads RW0, and loads RW1.
# instrs multiply UB0 with RW0 into ACC0 and then move a matrix from HM0 to UB0.
# cleanup writes the result of the multiplication from ACC0 to UB1 and then HM2.
#     it also does another matmul to confirm that the weight queue is
#     switched. this involves reading HM3 into UB2, multiplying UB2 with RW1
#     into ACC1, writing ACC1 to UB3, and then writing UB3 to HM4.
def mmc_rhm_same_ub_yes_s(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 1 0 1", "RW 0", "RW 1"],
                       instrs=["MMC.S 0 0 1", "RHM 0 0 1"],
                       cleanup=["ACT 0 1 1", "WHM 2 1 1", 
                                "RHM 3 2 1", "MMC 1 2 1", "ACT 1 3 1", 
                                "WHM 4 3 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_rhm_same_ub_yes_s",
                       reset=True, absoluteaddrs=False)

# multiplying UB0 into ACC0, no .S, moving from HM0 to UB1 (different UB)
# setup reads HM1 into UB0 so that it has a value, loads RW0, and loads RW1.
# instrs multiply HM0 with RW0 into ACC0 and then move a matrix from HM0 to UB1.
# cleanup writes the result of the multiplication from ACC0 to UB2 and then HM3.
#     it also does another matmul to confirm that the weight queue isn't 
#     switched. this involves reading HM4 into UB3, multiplying UB3 with RW0
#     into ACC1, writing ACC1 to UB4, and then writing UB4 to HM5. Lastly, we 
#     have to write the result of the RHM into UB1 back to the HM (HM2).
def mmc_rhm_no_overlap_no_s(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 1 0 1", "RW 0", "RW 1"],
                       instrs=["MMC 0 0 1", "RHM 0 1 1"],
                       cleanup=["ACT 0 2 1", "WHM 3 2 1", 
                                "RHM 4 3 1", "MMC 1 3 1", "ACT 1 4 1", 
                                "WHM 5 4 1",
                                "WHM 2 1 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_rhm_no_overlap_no_s",
                       reset=True, absoluteaddrs=False)

# multiplying UB0 into ACC0, w/ .S, moving from HM0 to UB1 (different UB)
# setup reads HM1 into UB0 so that it has a value, loads RW0, and loads RW1.
# instrs multiply HM0 with RW0 into ACC0 and then move a matrix from HM0 to UB1.
# cleanup writes the result of the multiplication from ACC0 to UB2 and then HM3.
#     it also does another matmul to confirm that the weight queue is 
#     switched. this involves reading HM4 into UB3, multiplying UB3 with RW1
#     into ACC1, writing ACC1 to UB4, and then writing UB4 to HM5. Lastly, we 
#     have to write the result of the RHM into UB1 back to the HM (HM2).
def mmc_rhm_no_overlap_yes_s(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 1 0 1", "RW 0", "RW 1"],
                       instrs=["MMC.S 0 0 1", "RHM 0 1 1"],
                       cleanup=["ACT 0 2 1", "WHM 3 2 1", 
                                "RHM 4 3 1", "MMC 1 3 1", "ACT 1 4 1", 
                                "WHM 5 4 1",
                                "WHM 2 1 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_rhm_no_overlap_yes_s",
                       reset=True, absoluteaddrs=False)



### MMC-WHM TESTS ###
def run_all_mmc_whm():
    pass

# multiplying UB0 into ACC0, no .S, moving from UB0 to HM0 (same UB)
# setup reads HM1 into UB0 so that it has a different value, loads RW0 and RW1.
# instrs multiply UB0 with RW0 into ACC0 and then move a matrix from UB0 to HM0.
# cleanup writes the result of the multiplication from ACC0 to UB1 and then HM2.
#     it also does another matmul to confirm that the weight queue isn't
#     switched. this involves reading HM3 into UB2, multiplying UB2 with RW0
#     into ACC1, writing ACC1 to UB3, and then writing UB3 to HM4.
def mmc_whm_same_ub_no_s(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 1 0 1", "RW 0", "RW 1"],
                       instrs=["MMC 0 0 1", "WHM 0 0 1"],
                       cleanup=["ACT 0 1 1", "WHM 2 1 1", 
                                "RHM 3 2 1", "MMC 1 2 1", "ACT 1 3 1", 
                                "WHM 4 3 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_whm_same_ub_no_s",
                       reset=True, absoluteaddrs=False)

# multiplying UB0 into ACC0, w/ .S, moving from UB0 to HM0 (same UB)
# setup reads HM1 into UB0 so that it has a different value, loads RW0 and RW1.
# instrs multiply UB0 with RW0 into ACC0 and then move a matrix from UB0 to HM0.
# cleanup writes the result of the multiplication from ACC0 to UB1 and then HM2.
#     it also does another matmul to confirm that the weight queue is
#     switched. this involves reading HM3 into UB2, multiplying UB2 with RW1
#     into ACC1, writing ACC1 to UB3, and then writing UB3 to HM4.
def mmc_whm_same_ub_yes_s(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 1 0 1", "RW 0", "RW 1"],
                       instrs=["MMC.S 0 0 1", "WHM 0 0 1"],
                       cleanup=["ACT 0 1 1", "WHM 2 1 1", 
                                "RHM 3 2 1", "MMC 1 2 1", "ACT 1 3 1", 
                                "WHM 4 3 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_whm_same_ub_yes_s",
                       reset=True, absoluteaddrs=False)

# multiplying UB0 into ACC0, no .S, moving from UB0 to HM1 (different UB)
# setup reads HM1 into UB0 and HM2 into UB1 and loads RW0 and RW1.
# instrs multiply UB0 with RW0 into ACC0 and then move a matrix from UB1 to HM0.
# cleanup writes the result of the multiplication from ACC0 to UB2 and then HM3.
#    it also does another matmul to confirm that the weight queue isn't
#    switched. this involves reading HM4 into UB3, multiplying UB3 with RW0
#    into ACC1, writing ACC1 to UB4, and then writing UB4 to HM5.
def mmc_whm_no_overlap_no_s(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 1 0 1", "RHM 2 1 1", "RW 0", "RW 1"],
                       instrs=["MMC 0 0 1", "WHM 0 1 1"],
                       cleanup=["ACT 0 2 1", "WHM 3 2 1", 
                                "RHM 4 3 1", "MMC 1 3 1", "ACT 1 4 1", 
                                "WHM 5 4 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_whm_no_overlap_no_s",
                       reset=True, absoluteaddrs=False)

# multiplying UB0 into ACC0, w/ .S, moving from UB1 to HM0 (different UB)
# setup reads HM1 into UB0 and HM2 into UB1 and loads RW0 and RW1.
# instrs multiply UB0 with RW0 into ACC0 and then move a matrix from UB1 to HM0.
# cleanup writes the result of the multiplication from ACC0 to UB2 and then HM3.
#    it also does another matmul to confirm that the weight queue is
#    switched. this involves reading HM4 into UB3, multiplying UB3 with RW1
#    into ACC1, writing ACC1 to UB4, and then writing UB4 to HM5.
def mmc_whm_no_overlap_no_s(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 1 0 1", "RHM 2 1 1", "RW 0", "RW 1"],
                       instrs=["MMC.S 0 0 1", "WHM 0 1 1"],
                       cleanup=["ACT 0 2 1", "WHM 3 2 1", 
                                "RHM 4 3 1", "MMC 1 3 1", "ACT 1 4 1", 
                                "WHM 5 4 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_whm_no_overlap_no_s",
                       reset=True, absoluteaddrs=False)



### MMC-RW TESTS ###
def run_all_mmc_rw():
    pass

# multiplying UB0 into ACC0, no .S, reading from RW0, buffer starts empty
# setup reads HM0 into UB0. 
# instrs multiply UB0 with the fifo queue into ACC0 when there's nothing in the 
#     FIFO queue. Then load RW0 into the FIFO queue.
# cleanup writes the result of the multiplication from ACC0 to UB1 and then HM1.
#     it also does another matmul to confirm that the weight queue contains RW0
#     at the front position. this involves reading HM2 into UB2, multiplying
#     UB2 with RW0 into ACC1, writing ACC1 to UB3, and then writing UB3 to HM3.
def mmc_rw_empty_no_s(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 0 0 1"],
                       instrs=["MMC 0 0 1", "RW 0"],
                       cleanup=["ACT 0 1 1", "WHM 1 1 1", 
                                "RHM 2 2 1", "MMC 1 2 1", "ACT 1 3 1", 
                                "WHM 3 3 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_rw_empty_no_s",
                       reset=True, absoluteaddrs=False)

# multiplying UB0 into ACC0, w/ .S, reading from RW0, buffer starts empty
# setup reads HM0 into UB0. 
# instrs multiply UB0 with the fifo queue into ACC0 when there's nothing in the 
#     FIFO queue. Then load RW0 into the FIFO queue.
# cleanup writes the result of the multiplication from ACC0 to UB1 and then HM1.
#     it also does another matmul to confirm that the weight queue contains RW0
#     at the front position. this involves reading HM2 into UB2, multiplying
#     UB2 with RW0 into ACC1, writing ACC1 to UB3, and then writing UB3 to HM3.
def mmc_rw_empty_yes_s(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 0 0 1"],
                       instrs=["MMC.S 0 0 1", "RW 0"],
                       cleanup=["ACT 0 1 1", "WHM 1 1 1", 
                                "RHM 2 2 1", "MMC 1 2 1", "ACT 1 3 1", 
                                "WHM 3 3 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_rw_empty_no_s",
                       reset=True, absoluteaddrs=False)

# multiplying UB0 into ACC0, no .S, reading from RW0, buffer starts with one space
# setup reads RW0, RW1, and RW2 into the FIFO queue so that there's one slot 
#     left. it also reads HM0 into UB0.
# instrs multiply UB0 with the fifo queue into ACC0. Then load RW3 into the 
#     queue.
# cleanup writes the result of the multiplication from ACC0 to UB1 and then HM1.
#     it also does 4 more matmuls to process the rest of the FIFO queue (RW0, 
#     RW1, RW2, and RW3).
def mmc_rw_one_space_no_s(distance, bitwidth, matsize):
    return squish_test(setup=["RW 0", "RW 1", "RW 2", "RHM 0 0 1"],
                       instrs=["MMC 0 0 1", "RW 3"],
                       cleanup=["ACT 0 1 1", "WHM 1 1 1", 
                                "RHM 2 2 1", "MMC 1 2 1", "ACT 1 3 1", 
                                "WHM 3 3 1",
                                "RHM 4 4 1", "MMC 2 4 1", "ACT 2 5 1", 
                                "WHM 5 5 1",
                                "RHM 6 6 1", "MMC 3 6 1", "ACT 3 7 1", 
                                "WHM 7 7 1",
                                "RHM 8 8 1", "MMC 4 8 1", "ACT 4 9 1", 
                                "WHM 9 9 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_rw_one_space_no_s",
                       reset=True, absoluteaddrs=False)

# multiplying UB0 into ACC0, w/ .S, reading from RW0, buffer starts with one space
# setup reads RW0, RW1, and RW2 into the FIFO queue so that there's one slot 
#     left. it also reads HM0 into UB0.
# instrs multiply UB0 with the fifo queue into ACC0. Then load RW3 into the 
#     queue.
# cleanup writes the result of the multiplication from ACC0 to UB1 and then HM1.
#     it also does 3 more matmuls to process the rest of the FIFO queue (RW1, 
#     RW2, and RW3).
def mmc_rw_one_space_yes_s(distance, bitwidth, matsize):
    return squish_test(setup=["RW 0", "RW 1", "RW 2", "RHM 0 0 1"],
                       instrs=["MMC.S 0 0 1", "RW 3"],
                       cleanup=["ACT 0 1 1", "WHM 1 1 1", 
                                "RHM 2 2 1", "MMC 1 2 1", "ACT 1 3 1", 
                                "WHM 3 3 1",
                                "RHM 4 4 1", "MMC 2 4 1", "ACT 2 5 1", 
                                "WHM 5 5 1",
                                "RHM 6 6 1", "MMC 3 6 1", "ACT 3 7 1", 
                                "WHM 7 7 1",
                                "RHM 8 8 1", "MMC 4 8 1", "ACT 4 9 1", 
                                "WHM 9 9 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_rw_one_space_yes_s",
                       reset=True, absoluteaddrs=False)

# multiplying UB0 into ACC0, no .S, reading from RW0, buffer starts full
# setup reads RW0, RW1, RW2, and RW3 into the FIFO queue so that there's no 
#     space left. it also reads HM0 into UB0.
# instrs multiply UB0 with the fifo queue into ACC0. Then load RW4 into the
#     queue.
# cleanup writes the result of the multiplication from ACC0 to UB1 and then HM1.
#     it also does 4 more matmuls to process the rest of the FIFO queue (RW0,
#     RW1, RW2, and RW3 - or is the last one RW4? I'm not sure what it does or should do in this position. does it refuse to input after it's full, or does it just replace the 4th slot?)
def mmc_rw_full_no_s(distance, bitwidth, matsize):
    return squish_test(setup=["RW 0", "RW 1", "RW 2", "RW 3", "RHM 0 0 1"],
                       instrs=["MMC 0 0 1", "RW 4"],
                       cleanup=["ACT 0 1 1", "WHM 1 1 1", 
                                "RHM 2 2 1", "MMC 1 2 1", "ACT 1 3 1", 
                                "WHM 3 3 1",
                                "RHM 4 4 1", "MMC 2 4 1", "ACT 2 5 1", 
                                "WHM 5 5 1",
                                "RHM 6 6 1", "MMC 3 6 1", "ACT 3 7 1", 
                                "WHM 7 7 1",
                                "RHM 8 8 1", "MMC 4 8 1", "ACT 4 9 1", 
                                "WHM 9 9 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_rw_full_no_s",
                       reset=True, absoluteaddrs=False)

# multiplying UB0 into ACC0, w/ .S, reading from RW0, buffer starts full
# setup reads RW0, RW1, RW2, and RW3 into the FIFO queue so that there's no 
#     space left. it also reads HM0 into UB0.
# instrs multiply UB0 with the fifo queue into ACC0. Then load RW4 into the
#     queue.
# cleanup writes the result of the multiplication from ACC0 to UB1 and then HM1.
#     it also does 4 more matmuls to process the rest of the FIFO queue (RW1,
#     RW2, RW3, and RW4).
def mmc_rw_full_no_s(distance, bitwidth, matsize):
    return squish_test(setup=["RW 0", "RW 1", "RW 2", "RW 3", "RHM 0 0 1"],
                       instrs=["MMC 0 0 1", "RW 4"],
                       cleanup=["ACT 0 1 1", "WHM 1 1 1", 
                                "RHM 2 2 1", "MMC 1 2 1", "ACT 1 3 1", 
                                "WHM 3 3 1",
                                "RHM 4 4 1", "MMC 2 4 1", "ACT 2 5 1", 
                                "WHM 5 5 1",
                                "RHM 6 6 1", "MMC 3 6 1", "ACT 3 7 1", 
                                "WHM 7 7 1",
                                "RHM 8 8 1", "MMC 4 8 1", "ACT 4 9 1", 
                                "WHM 9 9 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_rw_full_no_s",
                       reset=True, absoluteaddrs=False)



### MMC-MMC TESTS ###
def run_all_mmc_mmc():
    pass

# multiplying UB0 into ACC0 no .S, multiplying UB1 into ACC1 no .S (different UB and ACC)
# setup reads HM0 into UB0 and HM1 into UB1. it also loads RW0 and RW1 into the
#     weight queue.
# instrs multiply UB0 with RW0 into ACC0 (no S) and UB1 with RW1 into ACC1 
#     (no S).
# cleanup writes the result of the multiplications from ACC0 and ACC1 to UB2 and
#     UB3, and then to HM2 and HM3. then it does two more matmuls to confirm 
#     that RW0 is still in the FIFO queue and RW1 is still next.
def mmc_mmc_diff_ub_diff_acc_no_s_no_s(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 0 0 1", "RHM 1 1 1", "RW 0", "RW 1"],
                       instrs=["MMC 0 0 1", "MMC 1 1 1"],
                       cleanup=["ACT 0 2 1", "ACT 1 3 1",
                                "WHM 2 2 1", "WHM 3 3 1",
                                "RHM 4 4 1", "MMC.S 2 4 1", "ACT 2 5 1", 
                                "WHM 5 5 1",
                                "RHM 6 6 1", "MMC.S 3 6 1", "ACT 3 7 1", 
                                "WHM 7 7 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_mmc_diff_ub_diff_acc_no_s_no_s",
                       reset=True, absoluteaddrs=False)

# multiplying UB0 into ACC0 no .S, multiplying UB1 into ACC1 w/ .S (different UB and ACC)
# setup reads HM0 into UB0 and HM1 into UB1. it also loads RW0 and RW1 into the
#     weight queue.
# instrs multiply UB0 with RW0 into ACC0 (no S) and UB1 with RW1 into ACC1
#     (with S).
# cleanup writes the result of the multiplications from ACC0 and ACC1 to UB2 and
#     UB3, and then to HM2 and HM3. then it does one more matmul to confirm
#     that RW1 is now at the front of the weight queue. 
def mmc_mmc_diff_ub_diff_acc_no_s_yes_s(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 0 0 1", "RHM 1 1 1", "RW 0", "RW 1"],
                       instrs=["MMC 0 0 1", "MMC.S 1 1 1"],
                       cleanup=["ACT 0 2 1", "ACT 1 3 1",
                                "WHM 2 2 1", "WHM 3 3 1",
                                "RHM 4 4 1", "MMC.S 2 4 1", "ACT 2 5 1", 
                                "WHM 5 5 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_mmc_diff_ub_diff_acc_no_s_yes_s",
                       reset=True, absoluteaddrs=False)

# multiplying UB0 into ACC0 w/ .S, multiplying UB1 into ACC1 no .S (different UB and ACC)
# setup reads HM0 into UB0 and HM1 into UB1. it also loads RW0 and RW1 into the
#     weight queue.
# instrs multiply UB0 with RW0 into ACC0 (with S) and UB1 with RW1 into ACC1
#     (no S).
# cleanup writes the result of the multiplications from ACC0 and ACC1 to UB2 and
#     UB3, and then to HM2 and HM3. then it does one more matmul to confirm
#     that RW1 is now at the front of the weight queue.
def mmc_mmc_diff_ub_diff_acc_yes_s_no_s(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 0 0 1", "RHM 1 1 1", "RW 0", "RW 1"],
                       instrs=["MMC.S 0 0 1", "MMC 1 1 1"],
                       cleanup=["ACT 0 2 1", "ACT 1 3 1",
                                "WHM 2 2 1", "WHM 3 3 1",
                                "RHM 4 4 1", "MMC.S 2 4 1", "ACT 2 5 1", 
                                "WHM 5 5 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_mmc_diff_ub_diff_acc_yes_s_no_s",
                       reset=True, absoluteaddrs=False)

# multiplying UB0 into ACC0 w/ .S, multiplying UB1 into ACC1 w/ .S (different UB and ACC)
# setup reads HM0 into UB0 and HM1 into UB1. it also loads RW0, RW1, and RW2 
#     into the weight queue.
# instrs multiply UB0 with RW0 into ACC0 (with S) and UB1 with RW1 into ACC1
#     (with S).
# cleanup writes the result of the multiplications from ACC0 and ACC1 to UB2 and
#     UB3, and then to HM2 and HM3. then it does one more matmul to confirm
#     that RW2 is now at the front of the weight queue.
def mmc_mmc_diff_ub_diff_acc_yes_s_yes_s(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 0 0 1", "RHM 1 1 1", "RW 0", "RW 1", "RW 2"],
                       instrs=["MMC.S 0 0 1", "MMC.S 1 1 1"],
                       cleanup=["ACT 0 2 1", "ACT 1 3 1",
                                "WHM 2 2 1", "WHM 3 3 1",
                                "RHM 4 4 1", "MMC.S 2 4 1", "ACT 2 5 1", 
                                "WHM 5 5 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_mmc_diff_ub_diff_acc_yes_s_yes_s",
                       reset=True, absoluteaddrs=False)

# multiplying UB0 into ACC0 no .S, multiplying UB0 into ACC1 no .S (same UB)
# setup reads HM0 into UB0 and loads RW0 and RW1 into the weight queue.
# instrs multiply UB0 with RW0 into ACC0 (no S) and UB0 with RW0 into ACC1 
#     (no S).
# cleanup writes the result of the multiplications from ACC0 and ACC1 to UB1 and
#     UB2, and then to HM1 and HM2. then it does two more matmuls to confirm 
#     that RW0 is still the front of the queue and RW1 still follows.
def mmc_mmc_same_ub_diff_acc_no_s_no_s(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 0 0 1", "RW 0", "RW 1"],
                       instrs=["MMC 0 0 1", "MMC 1 0 1"],
                       cleanup=["ACT 0 1 1", "ACT 1 2 1",
                                "WHM 1 1 1", "WHM 2 2 1",
                                "RHM 3 3 1", "MMC.S 2 3 1", "ACT 2 4 1", 
                                "WHM 4 4 1",
                                "RHM 5 5 1", "MMC.S 3 5 1", "ACT 3 6 1", 
                                "WHM 6 6 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_mmc_same_ub_diff_acc_no_s_no_s",
                       reset=True, absoluteaddrs=False)

# multiplying UB0 into ACC0 no .S, multiplying UB0 into ACC1 w/ .S (same UB)
# setup reads HM0 into UB0 and loads RW0 and RW1 into the weight queue.
# instrs multiply UB0 with RW0 into ACC0 (no S) and UB0 with RW0 into ACC1 
#     (w/ S).
# cleanup writes the result of the multiplications from ACC0 and ACC1 to UB1 and
#     UB2, and then to HM1 and HM2. then it does one more matmul to confirm
#     that RW1 is now at the front of the weight queue.
def mmc_mmc_same_ub_diff_acc_no_s_yes_s(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 0 0 1", "RW 0", "RW 1"],
                       instrs=["MMC 0 0 1", "MMC.S 1 0 1"],
                       cleanup=["ACT 0 1 1", "ACT 1 2 1",
                                "WHM 1 1 1", "WHM 2 2 1",
                                "RHM 3 3 1", "MMC.S 2 3 1", "ACT 2 4 1", 
                                "WHM 4 4 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_mmc_same_ub_diff_acc_no_s_yes_s",
                       reset=True, absoluteaddrs=False)

# multiplying UB0 into ACC0 w/ .S, multiplying UB0 into ACC1 no .S (same UB)
# setup reads HM0 into UB0 and loads RW0 and RW1 into the weight queue.
# instrs multiply UB0 with RW0 into ACC0 (w/ S) and UB0 with RW1 into ACC1 
#     (no S).
# cleanup writes the result of the multiplications from ACC0 and ACC1 to UB1 and
#     UB2, and then to HM1 and HM2. then it does one more matmul to confirm
#     that RW1 is now at the front of the weight queue.
def mmc_mmc_same_ub_diff_acc_yes_s_no_s(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 0 0 1", "RW 0", "RW 1"],
                       instrs=["MMC.S 0 0 1", "MMC 1 0 1"],
                       cleanup=["ACT 0 1 1", "ACT 1 2 1",
                                "WHM 1 1 1", "WHM 2 2 1",
                                "RHM 3 3 1", "MMC.S 2 3 1", "ACT 2 4 1", 
                                "WHM 4 4 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_mmc_same_ub_diff_acc_yes_s_no_s",
                       reset=True, absoluteaddrs=False)

# multiplying UB0 into ACC0 w/ .S, multiplying UB0 into ACC1 w/ .S (same UB)
# setup reads HM0 into UB0 and loads RW0, RW1, and RW2 into the weight queue.
# instrs multiply UB0 with RW0 into ACC0 (w/ S) and UB0 with RW1 into ACC1 
#     (w/ S).
# cleanup writes the result of the multiplications from ACC0 and ACC1 to UB1 and
#     UB2, and then to HM1 and HM2. then it does one more matmul to confirm
#     that RW2 is now at the front of the weight queue.
def mmc_mmc_same_ub_diff_acc_yes_s_yes_s(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 0 0 1", "RW 0", "RW 1", "RW 2"],
                       instrs=["MMC.S 0 0 1", "MMC.S 1 0 1"],
                       cleanup=["ACT 0 1 1", "ACT 1 2 1",
                                "WHM 1 1 1", "WHM 2 2 1",
                                "RHM 3 3 1", "MMC.S 2 3 1", "ACT 2 4 1", 
                                "WHM 4 4 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_mmc_same_ub_diff_acc_yes_s_yes_s",
                       reset=True, absoluteaddrs=False)

# multiplying UB0 into ACC0 no .S, multiplying UB1 into ACC0 no .S (same ACC)
# setup reads HM0 and HM1 into UB0 and UB1. it also loads RW0 and RW1.
# instrs multiply UB0 with RW0 into ACC0 (no S) and UB1 with RW0 into ACC0 
#     (no S).
# cleanup writes the result of the multiplication from ACC0 to UB2 and HM2. 
#    then it does two more matmuls to confirm that RW0 and RW1 are still in the 
#    queue.
def mmc_mmc_diff_ub_same_acc_no_s_no_s(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 0 0 1", "RHM 1 1 1", "RW 0", "RW 1"],
                       instrs=["MMC 0 0 1", "MMC 0 1 1"],
                       cleanup=["ACT 0 2 1", "WHM 2 2 1",
                                "RHM 3 3 1", "MMC.S 1 3 1", "ACT 1 4 1", 
                                "WHM 4 4 1",
                                "RHM 5 5 1", "MMC.S 2 5 1", "ACT 2 6 1", 
                                "WHM 6 6 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_mmc_diff_ub_same_acc_no_s_no_s",
                       reset=True, absoluteaddrs=False)

# multiplying UB0 into ACC0 no .S, multiplying UB1 into ACC0 w/ .S (same ACC)
# setup reads HM0 and HM1 into UB0 and UB1. it also loads RW0 and RW1.
# instrs multiply UB0 with RW0 into ACC0 (no S) and UB1 with RW0 into ACC0
#     (w/ S).
# cleanup writes the result of the multiplication from ACC0 to UB2 and HM2. then
#     it does one more matmul to confirm that RW1 is now at the front of the 
#     queue.
def mmc_mmc_diff_ub_same_acc_no_s_yes_s(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 0 0 1", "RHM 1 1 1", "RW 0", "RW 1"],
                       instrs=["MMC 0 0 1", "MMC.S 0 1 1"],
                       cleanup=["ACT 0 2 1", "WHM 2 2 1",
                                "RHM 3 3 1", "MMC.S 1 3 1", "ACT 1 4 1", 
                                "WHM 4 4 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_mmc_diff_ub_same_acc_no_s_yes_s",
                       reset=True, absoluteaddrs=False)

# multiplying UB0 into ACC0 w/ .S, multiplying UB1 into ACC0 no .S (same ACC)
# setup reads HM0 and HM1 into UB0 and UB1. it also loads RW0 and RW1.
# instrs multiply UB0 with RW0 into ACC0 (w/ S) and UB1 with RW1 into ACC0 
#     (no S).
# cleanup writes the result of the multiplication from ACC0 to UB2 and HM2. then
#     it does one more matmul to confirm that RW1 is now at the front of the
#     queue.
def mmc_mmc_diff_ub_same_acc_yes_s_no_s(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 0 0 1", "RHM 1 1 1", "RW 0", "RW 1"],
                       instrs=["MMC.S 0 0 1", "MMC 0 1 1"],
                       cleanup=["ACT 0 2 1", "WHM 2 2 1",
                                "RHM 3 3 1", "MMC.S 1 3 1", "ACT 1 4 1", 
                                "WHM 4 4 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_mmc_diff_ub_same_acc_yes_s_no_s",
                       reset=True, absoluteaddrs=False)

# multiplying UB0 into ACC0 w/ .S, multiplying UB1 into ACC0 w/ .S (same ACC)
# setup reads HM0 and HM1 into UB0 and UB1. it also loads RW0, RW1, and RW2.
# instrs multiply UB0 with RW0 into ACC0 (w/ S) and UB1 with RW1 into ACC0
#     (w/ S).
# cleanup writes the result of the multiplication from ACC0 to UB2 and HM2. then
#     it does one more matmul to confirm that RW2 is now at the front of the
#     queue.
def mmc_mmc_diff_ub_same_acc_yes_s_yes_s(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 0 0 1", "RHM 1 1 1", "RW 0", "RW 1", "RW 2"],
                       instrs=["MMC.S 0 0 1", "MMC.S 0 1 1"],
                       cleanup=["ACT 0 2 1", "WHM 2 2 1",
                                "RHM 3 3 1", "MMC.S 1 3 1", "ACT 1 4 1", 
                                "WHM 4 4 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_mmc_diff_ub_same_acc_yes_s_yes_s",
                       reset=True, absoluteaddrs=False)

# multiplying UB0 into ACC0 no .S, multiplying UB0 into ACC0 no .S (same ACC and UB)
# setup reads HM0 into UB0 and loads RW0 and RW1.
# instrs multiply UB0 with RW0 into ACC0 (no S) and UB0 with RW0 into ACC0 
#     (no S).
# cleanup writes the result of the multiplication from ACC0 to UB1 and HM1. then
#     it does two more matmuls to confirm that RW0 is still at the front of the 
#     queue and still followed by RW 1.
def mmc_mmc_same_ub_same_acc_no_s_no_s(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 0 0 1", "RW 0", "RW 1"],
                       instrs=["MMC 0 0 1", "MMC 0 0 1"],
                       cleanup=["ACT 0 1 1", "WHM 1 1 1",
                                "RHM 2 2 1", "MMC.S 1 2 1", "ACT 1 3 1", 
                                "WHM 3 3 1",
                                "RHM 4 4 1", "MMC.S 2 4 1", "ACT 2 5 1", 
                                "WHM 5 5 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_mmc_same_ub_same_acc_no_s_no_s",
                       reset=True, absoluteaddrs=False)

# multiplying UB0 into ACC0 no .S, multiplying UB0 into ACC0 w/ .S (same ACC and UB)
# setup reads HM0 into UB0 and loads RW0 and RW1.
# instrs multiply UB0 with RW0 into ACC0 (no S) and UB0 with RW0 into ACC0
#     (w/ S).
# cleanup writes the result of the multiplication from ACC0 to UB1 and HM1. then
#     it does one more matmul to confirm that RW1 is now at the front of the
#     queue.
def mmc_mmc_same_ub_same_acc_no_s_yes_s(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 0 0 1", "RW 0", "RW 1"],
                       instrs=["MMC 0 0 1", "MMC.S 0 0 1"],
                       cleanup=["ACT 0 1 1", "WHM 1 1 1",
                                "RHM 2 2 1", "MMC.S 1 2 1", "ACT 1 3 1", 
                                "WHM 3 3 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_mmc_same_ub_same_acc_no_s_yes_s",
                       reset=True, absoluteaddrs=False)

# multiplying UB0 into ACC0 w/ .S, multiplying UB0 into ACC0 no .S (same ACC and UB)
# setup reads HM0 into UB0 and loads RW0 and RW1.
# instrs multiply UB0 with RW0 into ACC0 (w/ S) and UB0 with RW1 into ACC0
#     (no S).
# cleanup writes the result of the multiplication from ACC0 to UB1 and HM1. then
#     it does one more matmul to confirm that RW1 is now at the front of the
#     queue.
def mmc_mmc_same_ub_same_acc_yes_s_no_s(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 0 0 1", "RW 0", "RW 1"],
                       instrs=["MMC.S 0 0 1", "MMC 0 0 1"],
                       cleanup=["ACT 0 1 1", "WHM 1 1 1",
                                "RHM 2 2 1", "MMC.S 1 2 1", "ACT 1 3 1", 
                                "WHM 3 3 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_mmc_same_ub_same_acc_yes_s_no_s",
                       reset=True, absoluteaddrs=False)

# multiplying UB0 into ACC0 w/ .S, multiplying UB0 into ACC0 w/ .S (same ACC and UB)
# setup reads HM0 into UB0 and loads RW0, RW1, and RW2.
# instrs multiply UB0 with RW0 into ACC0 (w/ S) and UB0 with RW1 into ACC0
#     (w/ S).
# cleanup writes the result of the multiplication from ACC0 to UB1 and HM1. then
#     it does one more matmul to confirm that RW2 is now at the front of the
#     queue.
def mmc_mmc_same_ub_same_acc_yes_s_yes_s(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 0 0 1", "RW 0", "RW 1", "RW 2"],
                       instrs=["MMC.S 0 0 1", "MMC.S 0 0 1"],
                       cleanup=["ACT 0 1 1", "WHM 1 1 1",
                                "RHM 2 2 1", "MMC.S 1 2 1", "ACT 1 3 1", 
                                "WHM 3 3 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_mmc_same_ub_same_acc_yes_s_yes_s",
                       reset=True, absoluteaddrs=False)



### MMC-ACT TESTS ###
def run_all_mmc_act():
    pass

# multiplying UB0 into ACC0 no .S, accumulate from ACC1 to UB1 (different UB and ACC)
# setup reads HM0 into UB0 and loads RW0 and RW1 into the weight queue. then it
#     loads HM3 into UB3 and multiplies UB3 with RW0 (no S) into ACC1 to prepare
#     for instr 2 to activate it.
# instrs multiply UB0 with RW0 into ACC0 (no S) and activate the result from 
#     ACC1 to UB1.
# cleanup writes the result of the multiplication from ACC0 to UB2 and HM2. then
#     it writes the result of the accumulation from UB1 to HM1. then it does two
#     more matmuls to confirm that RW0 is still at the front of the queue and
#     RW1 is still next.
def mmc_act_diff_ub_diff_acc_no_s(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 0 0 1", "RHM 3 3 1", "RW 0", "RW 1", 
                              "MMC 1 3 1"],
                       instrs=["MMC 0 0 1", "ACT 1 1 1"],
                       cleanup=["ACT 0 2 1", "WHM 2 2 1", "WHM 1 1 1",
                                "RHM 4 4 1", "MMC.S 2 4 1", "ACT 2 5 1", 
                                "WHM 5 5 1",
                                "RHM 6 6 1", "MMC.S 3 6 1", "ACT 3 7 1", 
                                "WHM 7 7 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_act_diff_ub_diff_acc_no_s",
                       reset=True, absoluteaddrs=False)

# multiplying UB0 into ACC0 w/ .S, accumulate from ACC1 to UB1 (different UB and ACC)
# setup reads HM0 into UB0 and loads RW0 and RW1 into the weight queue. then it
#     loads HM3 into UB3 and multiplies UB3 with RW0 (no S) into ACC1 to prepare
#     for instr 2 to activate it.
# instrs multiply UB0 with RW0 into ACC0 (w/ S) and activate the setup result 
#     from ACC1 to UB1.
# cleanup writes the result of the multiplication from ACC0 to UB2 and HM2. then
#     it writes the result of the accumulation from UB1 to HM1. then it does one
#     more matmul to confirm that RW1 is now at the front of the queue.
def mmc_act_diff_ub_diff_acc_yes_s(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 0 0 1", "RHM 3 3 1", "RW 0", "RW 1", 
                              "MMC 1 3 1"],
                       instrs=["MMC.S 0 0 1", "ACT 1 1 1"],
                       cleanup=["ACT 0 2 1", "WHM 2 2 1", "WHM 1 1 1",
                                "RHM 4 4 1", "MMC.S 2 4 1", "ACT 2 5 1", 
                                "WHM 5 5 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_act_diff_ub_diff_acc_yes_s",
                       reset=True, absoluteaddrs=False)

# multiplying UB0 into ACC0 no .S, accumulate from ACC1 to UB0 (same UB)
# setup reads HM0 into UB0 and loads RW0 and RW1 into the weight queue. then it
#     loads HM2 into UB2 and multiplies UB2 with RW0 (no S) into ACC1 to prepare
#     for instr 2 to activate it.
# instrs multiply UB0 with RW0 into ACC0 (no S) and activate the setup result
#     from ACC1 to UB0.
# cleanup writes the result of the multiplication from ACC0 to UB1 and HM1. then
#     it writes the result of the accumulation from UB0 to HM3. then it does two
#     more matmuls to confirm that RW0 is still at the front of the queue and
#     RW1 is still next.
def mmc_act_same_ub_diff_acc_no_s(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 0 0 1", "RHM 2 2 1", "RW 0", "RW 1", 
                              "MMC 1 2 1"],
                       instrs=["MMC 0 0 1", "ACT 1 0 1"],
                       cleanup=["ACT 0 1 1", "WHM 1 1 1", "WHM 3 0 1",
                                "RHM 4 4 1", "MMC.S 2 4 1", "ACT 2 5 1", 
                                "WHM 5 5 1",
                                "RHM 6 6 1", "MMC.S 3 6 1", "ACT 3 7 1", 
                                "WHM 7 7 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_act_same_ub_diff_acc_no_s",
                       reset=True, absoluteaddrs=False)

# multiplying UB0 into ACC0 w/ .S, accumulate from ACC1 to UB0 (same UB)
# setup reads HM0 into UB0 and loads RW0 and RW1 into the weight queue. then it
#     loads HM2 into UB2 and multiplies UB2 with RW0 (no S) into ACC1 to prepare
#     for instr 2 to activate it.
# instrs multiply UB0 with RW0 into ACC0 (w/ S) and activate the setup result
#     from ACC1 to UB0.
# cleanup writes the result of the multiplication from ACC0 to UB1 and HM1. then
#     it writes the result of the accumulation from UB0 to HM3. then it does one
#     more matmul to confirm that RW1 is now at the front of the queue.
def mmc_act_same_ub_diff_acc_yes_s(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 0 0 1", "RHM 2 2 1", "RW 0", "RW 1", 
                              "MMC 1 2 1"],
                       instrs=["MMC.S 0 0 1", "ACT 1 0 1"],
                       cleanup=["ACT 0 1 1", "WHM 1 1 1", "WHM 3 0 1",
                                "RHM 4 4 1", "MMC.S 2 4 1", "ACT 2 5 1", 
                                "WHM 5 5 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_act_same_ub_diff_acc_yes_s",
                       reset=True, absoluteaddrs=False)

# multiplying UB0 into ACC0 no .S, accumulate from ACC0 to UB1 (same ACC)
# setup reads HM0 into UB0 and loads RW0 and RW1 into the weight queue.
# instrs multiply UB0 with RW0 into ACC0 (no S) and write ACC0 to UB1.
# cleanup writes the result of the multiplication from UB1 to HM1. then it does
#     two more matmuls to confirm that RW0 is still at the front of the queue
#     and RW1 is still next.
def mmc_act_diff_ub_same_acc_no_s(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 0 0 1", "RW 0", "RW 1"],
                       instrs=["MMC 0 0 1", "ACT 0 1 1"],
                       cleanup=["WHM 1 1 1",
                                "RHM 2 2 1", "MMC.S 1 2 1", "ACT 1 3 1", 
                                "WHM 3 3 1",
                                "RHM 4 4 1", "MMC.S 2 4 1", "ACT 2 5 1", 
                                "WHM 5 5 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_act_diff_ub_same_acc_no_s",
                       reset=True, absoluteaddrs=False)

# multiplying UB0 into ACC0 w/ .S, accumulate from ACC0 to UB1 (same ACC)
# setup reads HM0 into UB0 and loads RW0 and RW1 into the weight queue.
# instrs multiply UB0 with RW0 into ACC0 (w/ S) and write ACC0 to UB1.
# cleanup writes the result of the multiplication from UB1 to HM1. then it does
#     one more matmul to confirm that RW1 is now at the front of the queue.
def mmc_act_diff_ub_same_acc_yes_s(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 0 0 1", "RW 0", "RW 1"],
                       instrs=["MMC.S 0 0 1", "ACT 0 1 1"],
                       cleanup=["WHM 1 1 1",
                                "RHM 2 2 1", "MMC.S 1 2 1", "ACT 1 3 1", 
                                "WHM 3 3 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_act_diff_ub_same_acc_yes_s",
                       reset=True, absoluteaddrs=False)

# multiplying UB0 into ACC0 no .S, accumulate from ACC0 to UB0 (same ACC and UB)
# setup reads HM0 into UB0 and loads RW0 and RW1.
# instrs multiply UB0 with RW0 into ACC0 (no S) and write ACC0 back to UB0.
# cleanup writes the result of the multiplication from UB0 to HM1. then it does
#     two more matmuls to confirm that RW0 is still at the front of the queue
#     and RW1 is still next.
def mmc_act_same_ub_same_acc_no_s(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 0 0 1", "RW 0", "RW 1"],
                       instrs=["MMC 0 0 1", "ACT 0 0 1"],
                       cleanup=["WHM 1 0 1",
                                "RHM 2 2 1", "MMC.S 1 2 1", "ACT 1 3 1", 
                                "WHM 3 3 1",
                                "RHM 4 4 1", "MMC.S 2 4 1", "ACT 2 5 1", 
                                "WHM 5 5 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_act_same_ub_same_acc_no_s",
                       reset=True, absoluteaddrs=False)

# multiplying UB0 into ACC0 w/ .S, accumulate from ACC0 to UB0 (same ACC and UB) 
# setup reads HM0 into UB0 and loads RW0 and RW1.
# instrs multiply UB0 with RW0 into ACC0 (w/ S) and write ACC0 back to UB0.
# cleanup writes the result of the multiplication from UB0 to HM1. then it does
#     one more matmul to confirm that RW1 is now at the front of the queue.
def mmc_act_same_ub_same_acc_yes_s(distance, bitwidth, matsize):
    return squish_test(setup=["RHM 0 0 1", "RW 0", "RW 1"],
                       instrs=["MMC.S 0 0 1", "ACT 0 0 1"],
                       cleanup=["WHM 1 0 1",
                                "RHM 2 2 1", "MMC.S 1 2 1", "ACT 1 3 1", 
                                "WHM 3 3 1"],
                       distance=distance, bitwidth=bitwidth, matsize=matsize,
                       name="mmc_act_same_ub_same_acc_yes_s",
                       reset=True, absoluteaddrs=False)



def run_all_act_rhm():
    pass

def run_all_act_whm():
    pass

def run_all_act_rw():
    pass

def run_all_act_mmc():
    pass

def run_all_act_act():
    pass


def run_all_squish_tests():
    pass

