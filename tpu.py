from pyrtl import *
from pyrtl.analysis import area_estimation, TimingAnalysis

from config import *
from decoder import decode
from matrix import MMU_top
from activate import act_top

# accumulator memories
acc_mems = []
for i in range(MATSIZE):
    acc_mems.append(MemBlock(bitwidth=32, addrwidth=ACC_ADDR_SIZE, max_write_ports=None, max_read_ports=None, name=f"acc_mems_{i}"))


############################################################
#  Control Signals
############################################################

accum_act_raddr = WireVector(ACC_ADDR_SIZE, "tpu_accum_act_raddr")  # Activate unit read address for accumulator buffers
weights_dram_in = Input(64*8, "tpu_weights_dram_in")  # Input signal from weights DRAM controller
weights_dram_valid = Input(1, "tpu_weights_dram_valid")  # Valid bit for weights DRAM signal
halt = Output(1, "tpu_halt")  # When raised, stop simulation


############################################################
#  Instruction Memory and PC
############################################################

# incr_amt = WireVector(DWIDTH) #TODO: is DWIDTH the data width (eg DWIDTH = 8 means 8-bit data in the matrix?)

IMem = MemBlock(bitwidth=INSTRUCTION_WIDTH, addrwidth=IMEM_ADDR_SIZE)
pc = Register(IMEM_ADDR_SIZE, "tpu_pc")
# probe(pc, 'pc')
pc.incr = WireVector(1, "tpu_pc.incr")
# with conditional_assignment:
#     with pc.incr:
#         pc.next |= pc + 1 #incr_amt
pc.incr <<= 1  # right now, increment the PC every cycle
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

dispatch_mm, dispatch_act, dispatch_rhm, dispatch_whm, dispatch_halt, ub_start_addr, ub_dec_addr, ub_dest_addr, rhm_dec_addr, whm_dec_addr, rhm_length, whm_length, mmc_length, act_length, act_type, accum_raddr, accum_waddr, accum_overwrite, switch_weights, weights_raddr, weights_read = decode(instr)

halt <<= dispatch_halt

############################################################
#  Matrix Multiply Unit
############################################################

ub_mm_raddr_sig, acc_out, mm_busy, mm_done = MMU_top(acc_mems=acc_mems, data_width=DWIDTH, matrix_size=MATSIZE, accum_size=ACC_ADDR_SIZE, ub_size=UB_ADDR_SIZE, start=dispatch_mm, start_addr=ub_start_addr, nvecs=mmc_length, dest_acc_addr=accum_waddr, overwrite=accum_overwrite, swap_weights=switch_weights, ub_rdata=UB2MM, accum_raddr=accum_act_raddr, weights_dram_in=weights_dram_in, weights_dram_valid=weights_dram_valid)

ub_mm_raddr <<= ub_mm_raddr_sig

############################################################
#  Activate Unit
############################################################

accum_raddr_sig, ub_act_waddr, act_out, ub_act_we, act_busy = act_top(start=dispatch_act, start_addr=accum_raddr, dest_addr=ub_dest_addr, nvecs=act_length, func=act_type, accum_out=acc_out, matsize=MATSIZE, pc=pc, acc_mems=acc_mems)
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
#  Read/Write Host Memory
############################################################

hostmem_raddr = Output(HOST_ADDR_SIZE, "tpu_raddr")
hostmem_rdata = Input(DWIDTH*MATSIZE, "tpu_hostmem_rdata")
hostmem_re = Output(1, "tpu_hostmem_re")
hostmem_waddr = Output(HOST_ADDR_SIZE, "tpu_hostmem_waddr")
hostmem_wdata = Output(DWIDTH*MATSIZE, "tpu_hostmem_wdata")
hostmem_we = Output(1, "tpu_hostmem_we")

# Write Host Memory control logic
whm_N = Register(len(whm_length), "tpu_whm_N")
whm_ub_raddr = Register(len(ub_dec_addr), "tpu_whm_ub_addr")
whm_addr = Register(len(whm_dec_addr), "tpu_whm_addr")
whm_busy = Register(1, "tpu_whm_busy")

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
rhm_busy = Register(1, "tpu_rhm_busy")
rhm_ub_waddr = Register(len(ub_dec_addr), "tpu_rhm_ub_waddr")
with conditional_assignment:
    with dispatch_rhm:
        rhm_N.next |= rhm_length
        rhm_busy.next |= 1
        hostmem_raddr |= rhm_dec_addr
        hostmem_re |= 1
        rhm_addr.next |=  + 1
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

# probe(weights_raddr, "weights_raddr")
# probe(weights_read, "weights_read")

            
# probe(dispatch_mm, "dispatch_mm")
# probe(dispatch_act, "dispatch_act")
# probe(dispatch_rhm, "dispatch_rhm")
# probe(dispatch_whm, "dispatch_whm")

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
