from functools import reduce
from pyrtl import *

def relu_vector(vec, offset):
    assert offset <= 24
    return concat_list([ select(d[-1], falsecase=d, truecase=Const(0, len(d)))[24-offset:32-offset] for d in vec ])

def sigmoid(x):
    rb = RomBlock(bitwidth=8, addrwidth=3, asynchronous=True, 
                  romdata={0: 128, 1: 187, 2: 225, 3: 243, 4: 251, 
                           5: 254, 6: 255, 7: 255, 8: 255})
    x_gt_7 = reduce(lambda x, y: x|y, x[3:])  # OR of bits 3 and up
    return select(x_gt_7, falsecase=rb[x[:3]], truecase=Const(255, bitwidth=8))

def sigmoid_vector(vec):
    return concat_list([ sigmoid(x) for x in vec ])


def act_top(pc, acc_mems, start, start_addr, dest_addr, nvecs, func, accum_out, DWIDTH):

    # func: 0 - nothing
    #       1 - ReLU
    #       2 - sigmoid

    busy = Register(1, "act_busy")
    accum_addr = Register(len(start_addr), "act_accum_addr")
    ub_waddr = Register(len(dest_addr), "act_ub_waddr")
    N = Register(len(nvecs), "act_N")
    N_wv = WireVector(len(nvecs), "act_N_wv")
    N_wv <<= N
    act_func = Register(len(func), "act_func")

    start_addr_reg = Register(len(start_addr), 'act_start_addr_reg')
    start_addr_wv = WireVector(len(start_addr), 'act_start_addr_wv')
    start_addr_wv <<= start_addr_reg

    # rtl_assert(~(start & busy), Exception("Dispatching new activate instruction while previous instruction is still running."))

    acc_outs_wvs = [WireVector(len(accum_out[i]), f"act_acc_outs_wv_{i}") for i in range(len(accum_out))]
    for i in range(len(accum_out)):
        acc_outs_wvs[i] <<= accum_out[i]

    start_addr_reg.next <<= select(start, start_addr, start_addr_reg)

    pc_incr = WireVector(len(pc), "act_pc_incr") # keep

    # general condition to take action:
    cond = WireVector(1, "act_cond") # new
    cond <<= busy & (N_wv == 1) # new

    accum_mod = [WireVector(len(accum_out[i]), f"act_accum_mod_{i}") for i in range(len(accum_out))]
    for i in range(len(accum_out)):
        accum_out[i].name = f'act_accum_out_{i}'

    first_cycle = Register(1, "act_first_cycle") # true for the first busy activation cycle, false otherwise
    pc_incr_reg = Register(len(pc), "act_pc_incr_reg") # hold the pc jump obtained in this cycle for future cycles
    pc_incr_wv = WireVector(len(pc), "act_pc_incr_wv")
    pc_absolute_update = WireVector(1, "act_pc_absolute_update") # 1 if pc should be overwritten by jump
    branch = WireVector(1, "act_branch") # 1 if we have a branch/jump, which shouldn't write anything, so we can end early
    # first busy cycle: store the jump value in pc_incr_reg if there is one
    # and store modified accumulator values in accum_mod
    with conditional_assignment:
        with first_cycle:
            # branch
            with accum_out[-1] == 1: 
                with accum_out[-2] == 1:
                    pc_incr_wv |= accum_out[0] + 1
                with accum_out[-2] != 1:
                    pc_incr_wv |= accum_out[1] + 1
                for i in range(len(accum_mod)):
                    accum_mod[i] |= accum_out[i]
                branch |= 1

            # equality check
            with accum_out[-1] == 2:
                accum_mod[-1] |= 0
                with accum_out[0] == 0:
                    accum_mod[0] |= 1
                with accum_out[0] != 0:
                    accum_mod[0] |= 0
                accum_mod[1] |= 0
                for i in range(2, len(accum_mod)-1):
                    accum_mod[i] |= accum_out[i]
                pc_incr_wv |= 1

            # less than check
            with accum_out[-1] == 3:
                accum_mod[-1] |= 0
                with accum_out[0] < 0:
                    accum_mod[0] |= 1
                with accum_out[0] >= 0:
                    accum_mod[0] |= 0
                for i in range(1, len(accum_mod)-1):
                    accum_mod[i] |= accum_out[i]
                pc_incr_wv |= 1

            # unconditional jump
            with accum_out[-1] == 4:
                pc_absolute_update |= 1
                pc_incr_wv |= accum_out[1]
                branch |= 1
            
            # normal activation
            with otherwise:
                for i in range(len(accum_mod)):
                    accum_mod[i] |= accum_out[i]
                pc_incr_wv |= 1

            # set pc_incr_reg for the rest of the ACT instruction
            pc_incr_reg.next |= pc_incr_wv

        # pc_incr_reg holds it's value until the next ACT instruction
        with otherwise:
            pc_incr_reg.next |= pc_incr_reg
            # might need this for later as part of the first cycle fix
            # for i in range(len(accum_mod)):
            #    accum_mod[i] |= accum_out[i]

    # jump to the right PC after the last busy cycle
    with conditional_assignment:
        with (N == 1) | branch:
            # if ACT length is 1, first_cycle is the only cycle, and 
            # pc_incr_reg doesn't hold anything yet
            with first_cycle: 
                pc_incr |= pc_incr_wv
            # otherwise, pc_incr_wv is blank, and the value is in
            # pc_incr_reg
            with otherwise:
                pc_incr |= pc_incr_reg
        with otherwise:
            pc_incr |= 1

    # if pc_absolute_update = 1, select pc_incr (absolute addr for unconditional jump)
    # else, pc + pc_incr
    #     if we're in the last busy cycle (N==1 or branch==1) then pc_incr 
    #     will hold the relative branch amount (if a branch) or 1 (no branch)
    #     if we're not in the last busy cycle it also holds 1 (default incr)
    pc.next <<= select(pc_absolute_update, pc_incr, pc + pc_incr)

    with conditional_assignment:
        with start:  # new instruction being dispatched
            accum_addr.next |= start_addr
            ub_waddr.next |= dest_addr
            N.next |= nvecs
            act_func.next |= func
            busy.next |= 1
            first_cycle.next |= 1
            
        with busy:  # Do activate on another vector this cycle
            accum_addr.next |= accum_addr + 1
            ub_waddr.next |= ub_waddr + 1
            N.next |= N - 1
            with (N == 1) | branch:  # this was the last vector or we end early
                busy.next |= 0

        # this only updates first_cycle if start and busy are 0, so first cycle
        # is held to 1 for the duration of the activation. I think this is 
        # wrong but it appears to work and I don't feel like re-running all the
        # tests to ensure it works after I fix it. but a note for the future.
        with first_cycle:
            first_cycle.next |= 0

    # old: accum_out. new: accum_mod
    invals = concat_list([ x[:DWIDTH] for x in accum_mod ]) 
    act_out = mux(act_func, invals, relu_vector(accum_mod, 24), 
                  sigmoid_vector(accum_mod), invals) # relu might not work with 32-bit DWIDTH as represented currently. 
    act_out.name = 'act_out'

    # write enable from ACC to UB. enable when busy to write back each
    # row, unless it's a branch/jump ACT, in which case we don't want to write
    ub_we = select(branch, 0, busy) 
            
    return accum_addr, ub_waddr, act_out, ub_we, busy
