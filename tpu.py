import math
from pyrtl import *
from pyrtl.analysis import area_estimation, TimingAnalysis



def tpu(MATSIZE, HOST_ADDR_SIZE, UB_ADDR_SIZE, WEIGHT_DRAM_ADDR_SIZE, 
        ACC_ADDR_SIZE, DWIDTH, INSTRUCTION_WIDTH, IMEM_ADDR_SIZE, 
        HAZARD_DETECTION):
    from decoder import decode
    from matrix import MMU_top
    from activate import act_top

    # accumulator memories
    acc_mems = []
    for i in range(MATSIZE):
        acc_mems.append(MemBlock(bitwidth=DWIDTH, addrwidth=ACC_ADDR_SIZE, 
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

    UBuffer = MemBlock(bitwidth=MATSIZE*DWIDTH, addrwidth=UB_ADDR_SIZE, 
                       max_write_ports=2, max_read_ports=3)

    # Address and data wires for MM read port
    ub_mm_raddr = WireVector(UBuffer.addrwidth, "tpu_ub_mm_raddr")  # MM UB read address
    UB2MM = UBuffer[ub_mm_raddr]

    ############################################################
    #  Decoder
    ############################################################
    
    rhm_busy = Register(1, "tpu_rhm_busy")
    whm_busy = Register(1, "tpu_whm_busy")
    act_busy = Register(1, "tpu_act_busy")
    
    if HAZARD_DETECTION:
        mmc_busy = Register(1, "tpu_mmc_busy") 
        rw_busy = Register(1, "tpu_rw_busy")

        dispatch_mm, dispatch_act, dispatch_rhm, dispatch_whm, dispatch_halt, \
            dispatch_nop, ub_start_addr, ub_dec_addr, ub_dest_addr, \
            rhm_dec_addr, whm_dec_addr, rhm_length, whm_length, mmc_length, \
            act_length, act_type, accum_raddr, accum_waddr, accum_overwrite, \
            switch_weights, weights_raddr, weights_read, rhm_switch, rhm_conv, \
            whm_switch = decode(instr, HAZARD_DETECTION, mmc_busy, act_busy, 
                                rhm_busy, whm_busy, rw_busy, pc)

    elif not HAZARD_DETECTION:
        dispatch_mm, dispatch_act, dispatch_rhm, dispatch_whm, dispatch_halt, \
            ub_start_addr, ub_dec_addr, ub_dest_addr, rhm_dec_addr, \
            whm_dec_addr, rhm_length, whm_length, mmc_length, act_length, \
            act_type, accum_raddr, accum_waddr, accum_overwrite, \
            switch_weights, weights_raddr, weights_read, rhm_switch, rhm_conv, \
            whm_switch = decode(instr, HAZARD_DETECTION)

    halt <<= dispatch_halt

    ############################################################
    #  Matrix Multiply Unit
    ############################################################

    ub_mm_raddr_sig, acc_out, buf4, buf3, buf2, buf1 = MMU_top(
        acc_mems=acc_mems, data_width=DWIDTH, matrix_size=MATSIZE, 
        accum_size=ACC_ADDR_SIZE, ub_size=UB_ADDR_SIZE, start=dispatch_mm, 
        start_addr=ub_start_addr, nvecs=mmc_length, dest_acc_addr=accum_waddr, 
        overwrite=accum_overwrite, swap_weights=switch_weights, ub_rdata=UB2MM, 
        accum_raddr=accum_act_raddr, weights_dram_in=weights_dram_in, 
        weights_dram_valid=weights_dram_valid, MATSIZE=MATSIZE, DWIDTH=DWIDTH, 
        HAZARD_DETECTION=HAZARD_DETECTION)

    ub_mm_raddr <<= ub_mm_raddr_sig

    if HAZARD_DETECTION:
        # prevent new instructions from being dispatched while MMC instr is 
        # running. max MMC duration is 2*matsize + MMC length + 6.
        # mmc_cycles should start at that minus 1.
        mmc_N = Register(len(mmc_length), "tpu_mmc_N")
        mmc_cycles = Const(2*MATSIZE + 5) + mmc_length
        with conditional_assignment:
            with dispatch_mm:
                mmc_busy.next |= 1
                mmc_N.next |= mmc_cycles
            with mmc_busy:
                mmc_N.next |= mmc_N - 1
                with mmc_N == 1:
                    mmc_busy.next |= 0
    
    ############################################################
    #  Read/Write Host Memory
    ############################################################

    hostmem_raddr = Output(HOST_ADDR_SIZE, "tpu_hostmem_raddr")
    hostmem_rdata = Input(DWIDTH*MATSIZE, "tpu_hostmem_rdata")
    hostmem_re = Output(1, "tpu_hostmem_re")
    hostmem_waddr = Output(HOST_ADDR_SIZE, "tpu_hostmem_waddr")
    hostmem_wdata = Output(DWIDTH*MATSIZE, "tpu_hostmem_wdata")
    hostmem_we = Output(1, "tpu_hostmem_we")
    hostmem_raddr_whm = WireVector(HOST_ADDR_SIZE, "tpu_hostmem_raddr_whm")

    # split addr buffer into vec (row) and col
    addrbuf = WireVector(DWIDTH, "tpu_addrbuf")
    addrbuf <<= UBuffer[2**UB_ADDR_SIZE-1][0:DWIDTH]
    split_point = int(math.log(MATSIZE, 2)) 
    vec_addr = WireVector(DWIDTH-split_point, "tpu_addrbuf_vec")
    vec_addr <<= addrbuf[split_point:]
    col_addr = WireVector(split_point, "tpu_addrbuf_col")
    col_addr <<= addrbuf[0:split_point]

    # Write Host Memory control logic
    whm_N = Register(len(whm_length), "tpu_whm_N")
    whm_ub_raddr = Register(len(ub_dec_addr), "tpu_whm_ub_addr")
    whm_addr = Register(len(whm_dec_addr), "tpu_whm_addr")
    whm_src = Register(1, "tpu_whm_src_reg")
    whm_read_hm = WireVector(1, "tpu_whm_read_hm")
    
    # prevent new instructions from being dispatched while WHM instr is running.
    # max WHM duration is WHM length + 1.
    # whm_N should start at that minus 1.
    with conditional_assignment:
        with dispatch_whm:
            with whm_switch:
                with whm_length == 0: # HM[vec_addr][col] = UB[src_addr][0]
                    whm_N.next |= 1
                    whm_ub_raddr.next |= ub_dec_addr
                    whm_addr.next |= vec_addr
                    whm_busy.next |= 1
                    whm_src.next |= 1
                    whm_read_hm |= 1
                    hostmem_raddr_whm |= vec_addr
                with otherwise: # HM[vec_addr:vec_addr+len] = UB[src_addr:src_addr+len]
                    whm_N.next |= whm_length
                    whm_ub_raddr.next |= ub_dec_addr
                    whm_addr.next |= vec_addr
                    whm_busy.next |= 1
                    whm_src.next |= 0
            with otherwise: # normal: HM[dest_addr:dest_addr+len] = UB[dest_addr:dest_addr+len]
                whm_N.next |= whm_length
                whm_ub_raddr.next |= ub_dec_addr
                whm_addr.next |= whm_dec_addr
                whm_busy.next |= 1
                whm_src.next |= 0

        with whm_busy:
            whm_N.next |= whm_N - 1
            whm_ub_raddr.next |= whm_ub_raddr + 1
            whm_addr.next |= whm_addr + 1
            hostmem_we |= 1
            with whm_N == 1:
                whm_busy.next |= 0

    # prepare write to HM

    # store UB row
    ubuffer_out = WireVector(bitwidth=MATSIZE*DWIDTH, name="tpu_ubuffer_out")
    ubuffer_out <<= UBuffer[whm_ub_raddr]

    # write UB[UB row][0] to HM[vec_addr][col] without modifying other cells in
    # HM[vec_addr], using bitmasks
    whm_mask = WireVector(DWIDTH*MATSIZE, "tpu_whm_mask")
    whm_mask <<= ~shift_left_logical(Const(2**DWIDTH-1, DWIDTH*MATSIZE), DWIDTH*col_addr)
    whm_write_cell = WireVector(DWIDTH, "tpu_whm_write_cell")
    whm_write_cell <<= ubuffer_out[0:DWIDTH] 
    write_data = WireVector(DWIDTH*MATSIZE, "tpu_whm_write_data")
    write_data <<= shift_left_logical(whm_write_cell.zero_extended(bitwidth=DWIDTH*MATSIZE), DWIDTH*col_addr)

    # update HM write address and write data - choose between normal ubuffer
    # and masked write
    hostmem_waddr <<= whm_addr
    hostmem_wdata <<= mux(whm_src, ubuffer_out, (hostmem_rdata & whm_mask) | write_data)

    # Read Host Memory control logic
    # prevent new instructions from being dispatched while RHM instr is running.
    # max RHM duration is RHM length + 1.
    # rhm_N should start at that minus 1.
    # probe(rhm_length, "rhm_length")
    rhm_N = Register(len(rhm_length), "tpu_rhm_N")
    rhm_addr = Register(len(rhm_dec_addr), "tpu_rhm_addr")
    rhm_ub_waddr = Register(len(ub_dec_addr), "tpu_rhm_ub_waddr")
    rhm_src = Register(2, "tpu_rhm_src")
    # it should be pc+2. this works correctly in N mode (sort of) but in H mode,
    # this is happening one cycle after RHM dispatch, meaning pc has already 
    # been incremented by 1 and only needs 1 to be added.
    rhm_pc_payload = WireVector(DWIDTH*MATSIZE, name="tpu_rhm_pc_payload")
    rhm_pc_payload <<= concat_list([Const(0, DWIDTH), 
                                    (pc + 1)[:DWIDTH].sign_extended(DWIDTH), 
                                    Const(0, DWIDTH * (MATSIZE - 3)), 
                                    Const(4, DWIDTH)])

    # HM read enable during RHM or a WHM variant:
    # HM[vec_addr][col] = UB[src_addr][0]
    with conditional_assignment:
        with dispatch_rhm | rhm_busy | (dispatch_whm & whm_switch & whm_length == 0):
            hostmem_re |= 1 

    hostmem_raddr_rhm = WireVector(HOST_ADDR_SIZE, "tpu_hostmem_raddr_rhm")
    with conditional_assignment:
        with dispatch_rhm:
            rhm_busy.next |= 1
            rhm_ub_waddr.next |= ub_dec_addr
            with rhm_switch:
                with rhm_length == 0: #UB[ub_dec_addr] = [HM[vec_addr][col], 0, ..., 0]
                    rhm_N.next |= 1
                    hostmem_raddr_rhm |= vec_addr       
                    rhm_addr.next |= vec_addr + 1 # don't care?
                    rhm_src.next |= 1
                with otherwise: #UB[ub_dec_addr:ub_dec_addr+len] = HM[vec_addr:vec_addr+len]
                    rhm_N.next |= rhm_length
                    hostmem_raddr_rhm |= vec_addr
                    rhm_addr.next |= vec_addr + 1
                    rhm_src.next |= 0
            with rhm_conv: #UB[ub_dec_addr] = [0, pc+2, 0, ..., 0, 4] - for function returns
                rhm_N.next |= 1
                hostmem_raddr_rhm |= rhm_dec_addr # don't care?
                rhm_addr.next |= rhm_dec_addr + 1 # don't care?
                rhm_src.next |= 2
            with otherwise: # Normal: UB[ub_dec_addr:ub_dec_addr+len] = HM[rhm_dec_addr:rhm_dec_addr+len]
                rhm_N.next |= rhm_length
                hostmem_raddr_rhm |= rhm_dec_addr
                rhm_addr.next |= rhm_dec_addr + 1
                rhm_src.next |= 0
        
        with rhm_busy:
            rhm_N.next |= rhm_N - 1
            hostmem_raddr_rhm |= rhm_addr
            rhm_addr.next |= rhm_addr + 1
            rhm_ub_waddr.next |= rhm_ub_waddr + 1
            UBuffer[rhm_ub_waddr] |= mux(rhm_src, 
                                         hostmem_rdata,
                                         concat_list([shift_right_logical(hostmem_rdata, DWIDTH*col_addr)[0:DWIDTH], Const(0, DWIDTH * (MATSIZE-1))]),
                                         rhm_pc_payload, 
                                         default=0)
            with rhm_N == 1:
                rhm_busy.next |= 0

    hostmem_raddr <<= select(dispatch_rhm | rhm_busy, hostmem_raddr_rhm, 
                                                      hostmem_raddr_whm)

    ############################################################
    #  Activate Unit
    ############################################################
    
    # act_busy is None if HAZARD_DETECTION is False
    accum_raddr_sig, ub_act_waddr, act_out, ub_act_we, pc_update, \
        act_first_cycle, act_pc_absolute_update = act_top(start=dispatch_act,
        start_addr=accum_raddr, dest_addr=ub_dest_addr, nvecs=act_length, 
        func=act_type, accum_out=acc_out, pc=pc, acc_mems=acc_mems, 
        busy=act_busy, DWIDTH=DWIDTH, HAZARD_DETECTION=HAZARD_DETECTION)

    accum_act_raddr <<= accum_raddr_sig

    # Write the result of activate to the unified buffer, as long as RHM isn't
    # writing to the same UB address.
    with conditional_assignment:
        with ub_act_we & (~rhm_busy | (rhm_ub_waddr != ub_act_waddr)):
            UBuffer[ub_act_waddr] |= act_out

    # probe(ub_act_we, "ub_act_we")
    # probe(ub_act_waddr, "ub_act_waddr")
    # probe(act_out, "act_out")
    # probe(accum_raddr_sig, "accum_raddr")

    ############################################################
    #  Weights Memory
    ############################################################

    weights_dram_raddr = Output(WEIGHT_DRAM_ADDR_SIZE, "tpu_weights_dram_raddr")
    weights_dram_read = Output(1, "tpu_weights_dram_read")

    weights_dram_raddr <<= weights_raddr
    weights_dram_read <<= weights_read

    # in H mode, prevent new instructions from being dispatched while RW instr 
    # is running. max RW duration is max(1, ceil(matsize^2/64)) + 5.
    # rw_N should start at that minus 1.
    if HAZARD_DETECTION:
        rw_N = Register(len(weights_raddr), "tpu_rw_N")
        rw_cycles = Const(math.ceil(MATSIZE*MATSIZE/64)+4) 
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

    ############################################################
    #  Update PC
    ############################################################
    
    if HAZARD_DETECTION:
        with conditional_assignment:
            # normal PC increment following instruction dispatch
            with dispatch_mm | dispatch_rhm | dispatch_whm | weights_read | dispatch_nop:
                pc.next |= pc + 1
            # ACT increments PC in first busy cycle. can't increment in dispatch
            # because the increment isn't known yet 
            with dispatch_act: 
                pass
            with act_first_cycle: 
                pc.next |= select(act_pc_absolute_update, pc_update, 
                                                          pc + pc_update)

    # in N mode, pc_update holds 1 and act_pc_absolute is 0 by default, giving 
    # pc+1. pc_update holds or branch/jump amount after a branch/jump
    elif not HAZARD_DETECTION:
        pc.next <<= select(act_pc_absolute_update, pc_update, pc + pc_update)
    
    return IMem, UBuffer, weights_dram_in, weights_dram_valid, hostmem_rdata, \
        halt, hostmem_re, hostmem_raddr, hostmem_we, hostmem_waddr, \
        hostmem_wdata, weights_dram_read, weights_dram_raddr, acc_mems, buf4, \
        buf3, buf2, buf1, whm_src


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
