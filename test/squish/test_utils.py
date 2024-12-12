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



def run_all_rw_rhm():
    pass

def run_all_rw_whm():
    pass

def run_all_rw_rw():
    pass

def run_all_rw_mmc():
    pass

def run_all_rw_act():
    pass


def run_all_mmc_rhm():
    pass

def run_all_mmc_whm():
    pass

def run_all_mmc_rw():
    pass

def run_all_mmc_mmc():
    pass

def run_all_mmc_act():
    pass


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

