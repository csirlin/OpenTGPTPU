# Common utils for OpenTGPTPU
import numpy as np

def print_grid_mem_concise(mem, matsize):
    if mem.shape[0] == 0:
        print(" []")
        return

    max_num_width = max(len(str(np.min(mem))), len(str(np.max(mem))))
    max_index_width = len(str(mem.shape[0]))

    prev_row_zero = False
    for i in range(mem.shape[0]):
        curr_row_zero = np.array_equal(mem[i], [0]*matsize)
        if i < matsize or i == mem.shape[0]-1 or not curr_row_zero:
            print(" "*(max_index_width - len(str(i))), end="")
            print(f"{i}: [", end="")
            for j in range(matsize):
                if j != 0:
                    print(" ", end="")
                print(" "*(max_num_width - len(str(mem[i][j]))), end="")
                print(mem[i][j], end="")
            print("]")
            prev_row_zero = False
        elif not prev_row_zero:
            print("...") 
            prev_row_zero = True


def print_mems(host_memory, weight_memory, unified_buffer, fifo, accumulator,
               matsize):
    np.set_printoptions(threshold=np.inf, linewidth=300)

    print("Host memory:")
    print_grid_mem_concise(host_memory, matsize)

    print("Weight memory:\n", weight_memory, matsize)

    print("UBuffer:")
    print_grid_mem_concise(unified_buffer, matsize)

    print("FIFO Queue:\n", fifo)

    print("Accumulators:")
    print_grid_mem_concise(accumulator, matsize)


# compare a test and control memory to see if they're equal. if they're ever
# not equal, print the mismatched rows. return whether they're equal or not
def compare_mem(test_mem, ctrl_mem, name):
    if not np.array_equal(ctrl_mem, test_mem):
        print(f"Test failed ({name})")
        print("Control:") #  not sure I want to print this if I also print row-by-row, although printing the whole thing also prints the dtype which is nice
        print(ctrl_mem, ctrl_mem.dtype, ctrl_mem.shape)
        print("Test:")
        print(test_mem, test_mem.dtype, test_mem.shape)
        for i in range(min(len(test_mem), len(ctrl_mem))):
            if not np.array_equal(ctrl_mem[i], test_mem[i]):
                print(f"row {i}: Control: {ctrl_mem[i]}, Test: {test_mem[i]}")
        return False
    return True

def compare_all_mems(test_hostmem, test_weightsmem, test_ubuffer, test_wqueue, 
                     test_accmems,
                     ctrl_hostmem, ctrl_weightsmem, ctrl_ubuffer, ctrl_wqueue,
                     ctrl_accmems):
    hm = compare_mem(test_hostmem, ctrl_hostmem, "hostmem")
    wm = compare_mem(test_weightsmem, ctrl_weightsmem, "weightsmem")
    ub = compare_mem(test_ubuffer, ctrl_ubuffer, "ubuffer")
    wq = compare_mem(test_wqueue, ctrl_wqueue, "wqueue")
    ac = compare_mem(test_accmems, ctrl_accmems, "accmems")
    if not hm or not wm or not ub or not wq or not ac:
        return False
    return True

# run a test (runtpu and sim) with a specified program, hostmem, and weightmem. 
# give it a name, and specify where to put the test results, and bitwidth and
# matsize.
def run_and_compare_all_mems(prog_name, hm_name, wm_name, test_name, 
                             output_base,bitwidth, matsize):
    from runtpu import runtpu
    from sim import TPUSim

    test_hostmem, test_weightsmem, test_ubuffer, test_wqueue, test_accmems \
        = runtpu(prog_name, hm_name, wm_name, bitwidth, matsize, 
                    output_base + "runtpu", True)
    
    sim = TPUSim(prog_name, hm_name, wm_name, bitwidth, matsize, 
                    output_base + "sim")
    sim.run()
    ctrl_hostmem, ctrl_weightsmem, ctrl_ubuffer, ctrl_wqueue, ctrl_accmems \
        = sim.get_mems()
    
    if compare_all_mems(test_hostmem, test_weightsmem, test_ubuffer, 
                        test_wqueue, test_accmems, 
                        ctrl_hostmem, ctrl_weightsmem, ctrl_ubuffer, 
                        ctrl_wqueue, ctrl_accmems):
        print(f"Test {test_name} passed")
        return True
    else:
        print(f"Test {test_name} failed")
        return False
    
def load_and_compare_all_mems_combined(output_base):
    return load_and_compare_all_mems(output_base, "runtpu", output_base, "sim")
    
def load_and_compare_all_mems(output_base_1, group_name_1, output_base_2, group_name_2):
    test_hostmem, test_weightsmem, test_ubuffer, test_wqueue, test_accmems \
        = load_group_mems(output_base_1, group_name_1)
    ctrl_hostmem, ctrl_weightsmem, ctrl_ubuffer, ctrl_wqueue, ctrl_accmems \
        = load_group_mems(output_base_2, group_name_2)
    
    if compare_all_mems(test_hostmem, test_weightsmem, test_ubuffer, 
                        test_wqueue, test_accmems, ctrl_hostmem, 
                        ctrl_weightsmem, ctrl_ubuffer, ctrl_wqueue, 
                        ctrl_accmems):
        print(f"Test {output_base_1}/{group_name_1} vs {output_base_2}/{group_name_2} passed")
        return True
    else:
        print(f"Test {output_base_1} vs {output_base_2} failed")
        return False
    
def load_group_mems(output_base, group_name):
    with np.load(f"{output_base}/{group_name}.npz") as data:
        test_hm = data["hm"]
        test_wm = data["wm"]
        test_ur = data["ub"]
        test_wq = data["wq"]
        test_acc = data["acc"]
    return test_hm, test_wm, test_ur, test_wq, test_acc
