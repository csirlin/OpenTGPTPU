from pyrtl import *
import config
import isa

DATASIZE = config.DWIDTH
MATSIZE = config.MATSIZE
ACCSIZE = config.ACC_ADDR_SIZE

def decode(instruction):
    """
    :param instruction: instruction + optional operands + flags
    """

    accum_raddr = WireVector(ACCSIZE, "dec_accum_raddr")
    accum_waddr = WireVector(ACCSIZE, "dec_accum_waddr")
    accum_overwrite = WireVector(1, "dec_accum_overwrite")
    switch_weights = WireVector(1, "dec_switch_weights")
    weights_raddr = WireVector(config.WEIGHT_DRAM_ADDR_SIZE, "dec_weights_raddr")  # read address for weights DRAM
    weights_read = WireVector(1, "dec_weights_read")  # raised high to perform DRAM read

    ub_addr = WireVector(24, "dec_ub_addr")  # goes to FSM
    ub_raddr = WireVector(config.UB_ADDR_SIZE, "dec_ub_raddr")  # goes to UB read addr port
    ub_waddr = WireVector(config.UB_ADDR_SIZE, "dec_ub_waddr")

    whm_length = WireVector(8, "dec_whm_length")
    rhm_length = WireVector(8, "dec_rhm_length")
    mmc_length = WireVector(16, "dec_mmc_length")
    act_length = WireVector(8, "dec_act_length")
    act_type = WireVector(2, "dec_act_type")

    rhm_addr = WireVector(config.HOST_ADDR_SIZE, "dec_rhm_addr")
    whm_addr = WireVector(config.HOST_ADDR_SIZE, "dec_whm_addr")

    dispatch_mm = WireVector(1, "dec_dispatch_mm")
    dispatch_act = WireVector(1, "dec_dispatch_act")
    dispatch_rhm = WireVector(1, "dec_dispatch_rhm")
    dispatch_whm = WireVector(1, "dec_dispatch_whm")
    dispatch_halt = WireVector(1, "dec_dispatch_halt")

    # parse instruction
    op = instruction[ isa.OP_START*8 : isa.OP_END*8 ]
    #probe(op, "op")
    iflags = instruction[ isa.FLAGS_START*8 : isa.FLAGS_END*8 ]
    #probe(iflags, "flags")
    #probe(accum_overwrite, "decode_overwrite")
    ilength = instruction[ isa.LEN_START*8 : isa.LEN_END*8 ]
    memaddr = instruction[ isa.ADDR_START*8 : isa.ADDR_END*8 ]
    #probe(memaddr, "addr")
    ubaddr = instruction[ isa.UBADDR_START*8 : isa.UBADDR_END*8 ]
    #probe(ubaddr, "ubaddr")

    with conditional_assignment:
        with op == isa.OPCODE2BIN['NOP'][0]:
            pass
        with op == isa.OPCODE2BIN['WHM'][0]:
            dispatch_whm |= 1
            ub_raddr |= ubaddr
            whm_addr |= memaddr
            whm_length |= ilength
        with op == isa.OPCODE2BIN['RW'][0]:
            weights_raddr |= memaddr
            weights_read |= 1
        with op == isa.OPCODE2BIN['MMC'][0]:
            dispatch_mm |= 1
            ub_addr |= ubaddr
            accum_waddr |= memaddr
            mmc_length |= ilength
            accum_overwrite |= iflags[isa.OVERWRITE_BIT]
            switch_weights |= iflags[isa.SWITCH_BIT]
            # TODO: MMC may deal with convolution, set/clear that flag
        with op == isa.OPCODE2BIN['ACT'][0]:
            dispatch_act |= 1
            accum_raddr |= memaddr
            ub_waddr |= ubaddr
            act_length |= ilength
            act_type |= iflags[isa.ACT_FUNC_BITS]
            #probe(act_length, "act_length")
            #probe(act_type, "act_type")
            # TODO: ACT takes function select bits
        with op == isa.OPCODE2BIN['SYNC'][0]:
            pass
        with op == isa.OPCODE2BIN['RHM'][0]:
            dispatch_rhm |= 1
            rhm_addr |= memaddr
            ub_raddr |= ubaddr
            rhm_length |= ilength
        with op == isa.OPCODE2BIN['HLT'][0]:
            dispatch_halt |= 1

        #with otherwise:
        #    print("otherwise")

    return dispatch_mm, dispatch_act, dispatch_rhm, dispatch_whm, dispatch_halt, ub_addr, ub_raddr, ub_waddr, rhm_addr, whm_addr, rhm_length, whm_length, mmc_length, act_length, act_type, accum_raddr, accum_waddr, accum_overwrite, switch_weights, weights_raddr, weights_read
