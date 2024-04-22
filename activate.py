from functools import reduce

#import pyrtl
from pyrtl import *

def relu_vector(vec, offset):
    assert offset <= 24
    return concat_list([ select(d[-1], falsecase=d, truecase=Const(0, len(d)))[24-offset:32-offset] for d in vec ])

def sigmoid(x):
    rb = RomBlock(bitwidth=8, addrwidth=3, asynchronous=True, romdata={0: 128, 1: 187, 2: 225, 3: 243, 4: 251, 5: 254, 6: 255, 7: 255, 8: 255})
    x_gt_7 = reduce(lambda x, y: x|y, x[3:])  # OR of bits 3 and up
    return select(x_gt_7, falsecase=rb[x[:3]], truecase=Const(255, bitwidth=8))

def sigmoid_vector(vec):
    return concat_list([ sigmoid(x) for x in vec ])


def act_top(pc, acc_mems, start, start_addr, dest_addr, nvecs, func, accum_out, matsize):
    #, next_pc_reg):

    # func: 0 - nothing
    #       1 - ReLU
    #       2 - sigmoid

    busy = Register(1, "busy_acc")
    accum_addr = Register(len(start_addr))
    ub_waddr = Register(len(dest_addr))
    N = Register(len(nvecs))
    N_wv = WireVector(len(nvecs), "N_wv")
    N_wv <<= N
    act_func = Register(len(func), "act_func")
    start_acc_mems = []
    for i in range(matsize):
        start_acc_mems.append(Register(32, f"start_acc_mems_{i}"))
    start_addr_reg = Register(len(start_addr), 'start_addr_reg')
    start_addr_wv = WireVector(len(start_addr), 'start_addr_wv')
    start_addr_wv <<= start_addr_reg
    
    rtl_assert(~(start & busy), Exception("Dispatching new activate instruction while previous instruction is still running."))

    for i in range(len(start_acc_mems)):
        start_acc_mems[i].next <<= select(start, accum_out[i], start_acc_mems[i])

    start_addr_reg.next <<= select(start, start_addr, start_addr_reg)
    branch_enable = WireVector(32, "branch_enable")
    branch_enable <<= (acc_mems[-2][start_addr_reg])
    top_left = WireVector(32, "top_left")
    top_left <<= acc_mems[0][start_addr_reg]
    one_wv = WireVector(len(nvecs), "one_wv")
    one_wv <<= 1
    cond = WireVector(1, "act_cond")
    cond <<= busy & (N_wv == 1) & (branch_enable == 1) & (top_left == 0)
    pc_incr = concat_list([acc_mems[-4][start_addr_reg][4:8], acc_mems[-3][start_addr_reg]]) # WireVector(len(pc))
    # pc_incr[0:8] <<= acc_mems[-3][start_addr_reg]
    # pc_incr[8:] <<= acc_mems[-4][start_addr_reg][0:len(pc)-8]
    pc.next <<= select(0, (pc + pc_incr)[0:len(pc)], pc + 1)

    with conditional_assignment:
        with start:  # new instruction being dispatched
            accum_addr.next |= start_addr
            ub_waddr.next |= dest_addr
            N.next |= nvecs
            act_func.next |= func
            busy.next |= 1
            
        with busy:  # Do activate on another vector this cycle
            accum_addr.next |= accum_addr + 1
            ub_waddr.next |= ub_waddr + 1
            N.next |= N - 1
            with N == 1:  # this was the last vector
                busy.next |= 0

    invals = concat_list([ x[:8] for x in accum_out ])
    act_out = mux(act_func, invals, relu_vector(accum_out, 24), sigmoid_vector(accum_out), invals)
    act_out.name = 'act_out'
    #act_out = relu_vector(accum_out, 24)
    ub_we = busy
            
    return accum_addr, ub_waddr, act_out, ub_we, busy, start_addr_wv, cond, branch_enable, top_left, N_wv, act_func
