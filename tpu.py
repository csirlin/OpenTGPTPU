import math
from pyrtl import *
from pyrtl.analysis import area_estimation, TimingAnalysis



def tpu(MATSIZE, HOST_ADDR_SIZE, UB_ADDR_SIZE, WEIGHT_DRAM_ADDR_SIZE, 
        ACC_ADDR_SIZE, DWIDTH, INSTRUCTION_WIDTH, IMEM_ADDR_SIZE):
    from decoder import decode
    from matrix import MMU_top
    from activate import act_top

    # accumulator memories
    acc_mems = []
    for i in range(MATSIZE):
        acc_mems.append(MemBlock(bitwidth=32, addrwidth=ACC_ADDR_SIZE, 
                                max_write_ports=None, max_read_ports=None, 
                                name=f"acc_mems_{i}"))


    ############################################################
    #  Control Signals
    ############################################################

    accum_act_raddr = WireVector(ACC_ADDR_SIZE, "tpu_accum_act_raddr")  # Activate unit read address for accumulator buffers
    weights_dram_in = Input(64*DWIDTH, "tpu_weights_dram_in")  # Input signal from weights DRAM controller
    weights_dram_valid = Input(1, "tpu_weights_dram_valid")  # Valid bit for weights DRAM signal
    halt = Output(1, "tpu_halt")  # When raised, stop simulation


    ############################################################
    #  Instruction Memory and PC
    ############################################################

    # incr_amt = WireVector(DWIDTH) #TODO: is DWIDTH the data width (eg DWIDTH = 8 means 8-bit data in the matrix?)

    IMem = MemBlock(bitwidth=INSTRUCTION_WIDTH, addrwidth=IMEM_ADDR_SIZE)
    pc = Register(IMEM_ADDR_SIZE, "tpu_pc")
    # probe(pc, 'pc')
    instr = IMem[pc]
    # probe(instr, "instr")
    pc_out = Output(len(pc), "tpu_pc_out")
    pc_out <<= pc
            
    ############################################################
    #  Unified Buffer
    ############################################################

    UBuffer = MemBlock(bitwidth=MATSIZE*DWIDTH, addrwidth=UB_ADDR_SIZE, max_write_ports=2)

    # Address and data wires for MM read port
    ub_mm_raddr = WireVector(UBuffer.addrwidth, "tpu_ub_mm_raddr")  # MM UB read address
    UB2MM = UBuffer[ub_mm_raddr]

    ############################################################
    #  Decoder
    ############################################################

    mmc_busy = Register(1, "tpu_mmc_busy") 
    act_busy = Register(1, "tpu_act_busy")
    rhm_busy = Register(1, "tpu_rhm_busy")
    whm_busy = Register(1, "tpu_whm_busy")
    rw_busy = Register(1, "tpu_rw_busy")

    dispatch_mm, dispatch_act, dispatch_rhm, dispatch_whm, dispatch_halt, dispatch_nop, \
        ub_start_addr, ub_dec_addr, ub_dest_addr, rhm_dec_addr, whm_dec_addr, \
        rhm_length, whm_length, mmc_length, act_length, act_type, accum_raddr, \
        accum_waddr, accum_overwrite, switch_weights, weights_raddr, \
        weights_read = decode(instr, mmc_busy, act_busy, rhm_busy, whm_busy, rw_busy, pc)

    halt <<= dispatch_halt

    ############################################################
    #  Matrix Multiply Unit
    ############################################################

    ub_mm_raddr_sig, acc_out, mm_done, buf4, buf3, buf2, buf1 = MMU_top(
        acc_mems=acc_mems, data_width=DWIDTH, matrix_size=MATSIZE, 
        accum_size=ACC_ADDR_SIZE, ub_size=UB_ADDR_SIZE, start=dispatch_mm, 
        start_addr=ub_start_addr, nvecs=mmc_length, dest_acc_addr=accum_waddr, 
        overwrite=accum_overwrite, swap_weights=switch_weights, ub_rdata=UB2MM, 
        accum_raddr=accum_act_raddr, weights_dram_in=weights_dram_in, 
        weights_dram_valid=weights_dram_valid, MATSIZE=MATSIZE, DWIDTH=DWIDTH)

    ub_mm_raddr <<= ub_mm_raddr_sig

    # prevent new instructions from being dispatched while mmc unit is running
    mmc_N = Register(len(mmc_length), "tpu_mmc_N")
    mmc_cycles = Const(2*MATSIZE + 2) + mmc_length
    with conditional_assignment:
        with dispatch_mm:
            mmc_busy.next |= 1
            mmc_N.next |= mmc_cycles
        with mmc_busy:
            mmc_N.next |= mmc_N - 1
            with mmc_N == 1:
                mmc_busy.next |= 0

    ############################################################
    #  Activate Unit
    ############################################################

    accum_raddr_sig, ub_act_waddr, act_out, ub_act_we, pc_incr_wv, \
        act_first_cycle = act_top(start=dispatch_act, start_addr=accum_raddr, 
        dest_addr=ub_dest_addr, nvecs=act_length, func=act_type, 
        accum_out=acc_out, pc=pc, acc_mems=acc_mems, DWIDTH=DWIDTH, 
        busy=act_busy)

    accum_act_raddr <<= accum_raddr_sig

    # Write the result of activate to the unified buffer
    with conditional_assignment:
        with ub_act_we:
            UBuffer[ub_act_waddr] |= act_out

    # probe(ub_act_we, "ub_act_we")
    # probe(ub_act_waddr, "ub_act_waddr")
    # probe(act_out, "act_out")
    # probe(accum_raddr_sig, "accum_raddr")

    ############################################################
    #  Update PC
    ############################################################

    with conditional_assignment:
        with dispatch_mm | dispatch_rhm | dispatch_whm | weights_read | dispatch_nop:
            pc.next |= pc + 1
        with dispatch_act: # ACT increments PC only when branch is decided
            pass
        # pc_incr_wv is the branch amount. this shouldn't conflict with any 
        # dispatches because nothing should be ready for dispatch if 
        # act_first_cycle is true...
        with act_first_cycle: 
            pc.next |= pc + pc_incr_wv

    ############################################################
    #  Read/Write Host Memory
    ############################################################

    hostmem_raddr = Output(HOST_ADDR_SIZE, "tpu_hostmem_raddr")
    hostmem_rdata = Input(DWIDTH*MATSIZE, "tpu_hostmem_rdata")
    hostmem_re = Output(1, "tpu_hostmem_re")
    hostmem_waddr = Output(HOST_ADDR_SIZE, "tpu_hostmem_waddr")
    hostmem_wdata = Output(DWIDTH*MATSIZE, "tpu_hostmem_wdata")
    hostmem_we = Output(1, "tpu_hostmem_we")

    # Write Host Memory control logic
    whm_N = Register(len(whm_length), "tpu_whm_N")
    whm_ub_raddr = Register(len(ub_dec_addr), "tpu_whm_ub_addr")
    whm_addr = Register(len(whm_dec_addr), "tpu_whm_addr")

    ubuffer_out = UBuffer[whm_ub_raddr]

    hostmem_waddr <<= whm_addr
    hostmem_wdata <<= ubuffer_out

    with conditional_assignment:
        with dispatch_whm:
            whm_N.next |= whm_length
            whm_ub_raddr.next |= ub_dec_addr
            whm_addr.next |= whm_dec_addr
            whm_busy.next |= 1
        with whm_busy:
            whm_N.next |= whm_N - 1
            whm_ub_raddr.next |= whm_ub_raddr + 1
            whm_addr.next |= whm_addr + 1
            hostmem_we |= 1
            with whm_N == 1:
                whm_busy.next |= 0


    # Read Host Memory control logic
    # probe(rhm_length, "rhm_length")
    rhm_N = Register(len(rhm_length), "tpu_rhm_N")
    rhm_addr = Register(len(rhm_dec_addr), "tpu_rhm_addr")
    rhm_ub_waddr = Register(len(ub_dec_addr), "tpu_rhm_ub_waddr")
    # hostmem_raddr_reg = Register(HOST_ADDR_SIZE, "tpu_hostmem_raddr_reg")
    with conditional_assignment:
        with dispatch_rhm:
            rhm_N.next |= rhm_length
            rhm_busy.next |= 1
            hostmem_raddr |= rhm_dec_addr
            hostmem_re |= 1
            rhm_addr.next |= rhm_dec_addr + 1
            rhm_ub_waddr.next |= ub_dec_addr
        with rhm_busy:
            rhm_N.next |= rhm_N - 1
            hostmem_raddr |= rhm_addr
            hostmem_re |= 1
            rhm_addr.next |= rhm_addr + 1
            rhm_ub_waddr.next |= rhm_ub_waddr + 1
            UBuffer[rhm_ub_waddr] |= hostmem_rdata
            with rhm_N == 1:
                rhm_busy.next |= 0

    ############################################################
    #  Weights Memory
    ############################################################

    weights_dram_raddr = Output(WEIGHT_DRAM_ADDR_SIZE, "tpu_weights_dram_raddr")
    weights_dram_read = Output(1, "tpu_weights_dram_read")

    weights_dram_raddr <<= weights_raddr
    weights_dram_read <<= weights_read

    # prevent new instructions from being dispatched while fifo queue is working
    rw_N = Register(len(weights_raddr), "tpu_rw_N")
    rw_cycles = Const(math.ceil(MATSIZE*MATSIZE/64)+3) 
    with conditional_assignment:
        with weights_read: # basically dispatch_rw
            rw_N.next |= rw_cycles # stay busy for full duration
            rw_busy.next |= 1
        with rw_busy:
            rw_N.next |= rw_N - 1
            with rw_N == 1:
                rw_busy.next |= 0

    # probe(weights_raddr, "weights_raddr")
    # probe(weights_read, "weights_read")

                
    # probe(dispatch_mm, "dispatch_mm")
    # probe(dispatch_act, "dispatch_act")
    # probe(dispatch_rhm, "dispatch_rhm")
    # probe(dispatch_whm, "dispatch_whm")
    
    return IMem, UBuffer, weights_dram_in, weights_dram_valid, hostmem_rdata, \
        halt, hostmem_re, hostmem_raddr, hostmem_we, hostmem_waddr, \
        hostmem_wdata, weights_dram_read, weights_dram_raddr, acc_mems, buf4, \
        buf3, buf2, buf1, pc


def run_synth():
    print("logic = {:2f} mm^2, mem={:2f} mm^2".format(*area_estimation()))
    t = TimingAnalysis()
    print("Max freq = {} MHz".format(t.max_freq()))
    print("")
    print("Running synthesis...")
    synthesize()
    print("logic = {:2f} mm^2, mem={:2f} mm^2".format(*area_estimation()))
    t = TimingAnalysis()
    print("Max freq = {} MHz".format(t.max_freq()))
    print("")
    print("Running optimizations...")
    optimize()
    total = 0
    for gate in working_block():
        if gate.op in ('s', 'c'):
            pass
        total += 1
    print("Gate total: " + str(total))
    print("logic = {:2f} mm^2, mem={:2f} mm^2".format(*area_estimation()))
    t = TimingAnalysis()
    print("Max freq = {} MHz".format(t.max_freq()))

#run_synth()
