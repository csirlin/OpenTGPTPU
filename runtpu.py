from datetime import datetime
import math
import os
import pickle
from pyrtl import *
import argparse
import numpy as np

#set_debug_mode()

from tpu import tpu
import config
from utils import print_mems


# turns a vector of values into a single integer
# if bitwidth=8, then [a, b, c, d] -> (256^3)*d + (256^2)*c + (256)*b + a
def concat_vec(vec, bitwidth):
    t = 0
    mask = int('1'*bitwidth, 2)
    for x in reversed(vec):
        t = (t<<bitwidth) | (int(x) & mask)
    # print(vec, t)
    return t

# turns a 2d array (tile) of values into a single integer
# if bitwidth=8, then [[a, b], [c, d]] -> (256^3)*a + (256^2)*b + (256)*c + d
def concat_tile(tile, bitwidth):
    val = 0
    size = len(tile)
    mask = int('1'*bitwidth, 2)
    for row in tile:
        for x in row:
            val = (val<<bitwidth) | (int(x) & mask)
        #print_weight_mem({0:val})
    #return val & (size*size*bits)  # if negative, truncate bits to correct size
    return val

# turns a number into an appropriately lengthed vector of values in the 
# specified bitwidth
# if bitwidth=8, then (256^3)*1 + (256^2)*2 + (256)*3 + 4) -> [1, 2, 3, 4]
def make_vec(value, bitwidth):
    vec = []
    mask = int('1'*bitwidth, 2)
    while value > 0:
        vec.append(value & mask)
        value = value >> bitwidth
    return list(reversed(vec))

# like make_vec, but the number of values will always be matsize
def make_vec_2(value, bitwidth, matsize):
    vec = []
    mask = int('1'*bitwidth, 2)
    for i in range(matsize):
        vec.append(value & mask)
        value = value >> bitwidth
    return list(vec)

# make a matsize*matsize tile of bitwidth-sized values from a single value
# LSB is top-left corner, and it fills in normally from there.
def make_tile(value, bitwidth, matsize):
    tile = [[0] * matsize for _ in range(matsize)]
    mask = int('1'*bitwidth, 2)
    for i in range(matsize-1, -1, -1):
        for j in range(matsize-1, -1, -1):
            tile[i][j] = value & mask
            value = value >> bitwidth
    return tile

def print_mem(mem, bitwidth, matsize):
    ks = sorted(mem.keys())
    for a in ks:
        print(a, make_vec_2(mem[a], bitwidth, matsize))

def print_weight_mem(mem, bitwidth, matsize):
    ks = sorted(mem.keys())
    mask = int('1'*(matsize*bitwidth), 2)
    vecs = []
    for a in ks:
        vec = []
        tile = mem[a]
        while tile > 0:
            vec.append(make_vec(tile & mask, bitwidth))
            tile = tile >> (bitwidth*matsize) ###hmmm
        if vec != []:
            vecs.append(vec)
    for a, vec in enumerate(vecs):
        print(a, list(reversed(vec)))

def reverse_value(value, bitwidth):
    rev_val = 0
    mask = int('1'*bitwidth, 2)
    while value > 0:
        rev_val = (rev_val << bitwidth) | (value & mask)
        value = value >> bitwidth
    return rev_val

# convert hostmem to 2d numpy array
def hostmem_to_np(hostmem, bitwidth, matsize):
    keys = sorted(hostmem.keys())
    hostmem_np = np.zeros((keys[-1]+1, matsize))
    for k in keys:
        hostmem_np[k] = make_vec_2(hostmem[k], bitwidth, matsize)
    return hostmem_np.astype(int)

# convert weightsmem to 2d numpy array
def weightsmem_to_np(weightsmem, bitwidth, matsize):
    keys = sorted(weightsmem.keys())
    if len(keys) == 0:
        return np.zeros((0, matsize, matsize))
    weightsmem_np = np.zeros((keys[-1]+1, matsize, matsize))
    for k in keys:
        weightsmem_np[k] = make_tile(weightsmem[k], bitwidth, matsize)
    return weightsmem_np.astype(int)

# convert UBuffer to a 2d numpy array. convert the same number of rows as the 
# number of rows in the host memory
def ubuffer_to_np(sim, ubuffer, bitwidth, matsize, row_count):
    ubuffer_dict = sim.inspect_mem(ubuffer)
    keys = [k for k in sorted(ubuffer_dict.keys())]
    if len(keys) > 0:
        row_count = max(row_count, keys[-1]+1)

    ubuffer_np = np.zeros((row_count, matsize))
    for k in keys:
        vec = make_vec_2(ubuffer_dict[k], bitwidth, matsize)
        ubuffer_np[k] = vec
    return ubuffer_np.astype(int)

# convert weight queue to a 3d numpy array. each get converted to a 2d array of 
# size matsize x matsize. weight 0 is the front, weight 3 is the back.
def wqueue_to_np(sim, buf4, buf3, buf2, buf1, bitwidth, matsize):
    wqueue_np = np.zeros((4, matsize, matsize))
    for i, buf in enumerate([buf4, buf3, buf2]):
        buf_tile = make_tile(sim.inspect(buf), bitwidth, matsize)
        wqueue_np[i] = buf_tile

    buf1_val = 0
    for i in range(math.ceil(matsize*matsize/64)-1, -1, -1):
        buf1_val = (buf1_val << 64*bitwidth) | sim.inspect(buf1[i])
    buf1_tile = make_tile(buf1_val, bitwidth, matsize)
    wqueue_np[3] = buf1_tile

    full_slots = 0
    if sim.inspect('fifo_empty4') == 0: 
        full_slots += 1
    if sim.inspect('fifo_empty3') == 0:
        full_slots += 1
    if sim.inspect('fifo_empty2') == 0:
        full_slots += 1
    if sim.inspect('fifo_full') == 1:
        full_slots += 1

    return wqueue_np[:full_slots].astype(int)
    
# convert accumulator memory to a 2d numpy array. convert the same number of
# rows as the number of rows in the host memory
def accmem_to_np(sim, acc_mems, matsize, row_count):
    acc_mems_vals = [sim.inspect_mem(acc_mem) for acc_mem in acc_mems]

    keys = set()
    for i in range(len(acc_mems_vals)):
        keys = keys.union(set(acc_mems_vals[i].keys()))
    keys = sorted(list(keys))
    if len(keys) > 0:
        row_count = max(row_count, keys[-1]+1)
    accmem_np = np.zeros((row_count, matsize))
    for k in keys:
        for i in range(matsize):
            accmem_np[k][i] = acc_mems_vals[i].get(k, 0)
    return accmem_np.astype(int)


def runtpu(prog: str, hostmem_filename: str, weightsmem_filename: str, 
           bitwidth: int, matsize: int, output_folder: str, output_trace: bool):
    # Read the program and build an instruction list
    with open(prog, 'rb') as f:
        ins = [x for x in f.read()]  # create byte list from input

    instrs = []
    width = config.INSTRUCTION_WIDTH / 8
    # This assumes instructions are strictly byte-aligned

    for i in range(int(len(ins)/width)):  # once per instruction
        val = 0
        for j in range(int(width)):  # for each byte
            val = (val << 8) | ins.pop(0)
        instrs.append(val)

    #print(list(map(hex, instrs)))

    # Read the dram files and build memory images
    hostarray = np.load(hostmem_filename)
    # print("Host array:")
    # print(hostarray)
    host_shape = hostarray.shape
    # print(host_shape)
    if len(host_shape) == 3:
        flat_host = np.zeros((host_shape[0] * host_shape[1], host_shape[2]))
        # print(flat_host.shape)
        for i, arr in enumerate(hostarray):
            flat_host[host_shape[1]*i: host_shape[1]*(i+1)] = arr
    if len(host_shape) == 2:
        flat_host = hostarray
    # print("Flat host array:")
    # print(flat_host)
    hostmem = { a : concat_vec(vec, bitwidth) for a,vec in enumerate(flat_host) }
    # print("Host memory start:")
    # print(hostmem)
    # print_mem(hostmem)

    weightsarray = np.load(weightsmem_filename)
    # print("Weightsarray")
    # print(weightsarray)
    # print(weightsarray.shape)
    size = weightsarray.shape[-1]
    weight_shape = weightsarray.shape
    if len(weight_shape) == 3:
        weightsmem = { a : concat_tile(tile, bitwidth) for a,tile in enumerate(weightsarray) }
    if len(weight_shape) == 2:
        weightsmem = np.zeros(())
    #weightsmem = { a : concat_vec(vec, bitwidth) for a,vec in enumerate(weightsarray) }
    # print("Weight memory:")
    # print_weight_mem(weightsmem, size=size, bits=bitwidth)
    # print(weightsmem)

    '''
    Left-most element of each vector should be left-most in memory: use concat_list for each vector

    For weights mem, first vector goes last; hardware already handles this by iterating from back to front over the tile.
    The first vector should be at the "front" of the tile.

    For host mem, each vector goes at one address. First vector at address 0.
    '''
    tilesize = matsize * matsize  # number of weights in a tile
    nchunks = max(tilesize / 64, 1)  # Number of DRAM transfers needed from Weight DRAM for one tile
    # print(f"nchunks = {nchunks}")
    chunkmask = pow(2,64*bitwidth)-1

    def getchunkfromtile(tile, chunkn):
        #print("Get chunk: ", chunkn, nchunks, chunkmask, tile)
        #print((tile >> ((nchunks - chunkn - 1)*64*8)) & chunkmask)
        if chunkn >= nchunks:
            raise Exception("Reading more weights than are present in one tile?")
        return (tile >> int(((nchunks - chunkn - 1))*64*bitwidth)) & chunkmask

    reset_working_block()
    IMem, UBuffer, weights_dram_in, weights_dram_valid, hostmem_rdata, halt, \
        hostmem_re, hostmem_raddr, hostmem_we, hostmem_waddr, hostmem_wdata, \
        weights_dram_read, weights_dram_raddr, acc_mems, buf4, buf3, buf2, buf1, \
        whm_src = tpu(matsize, config.HOST_ADDR_SIZE, config.UB_ADDR_SIZE, 
        config.WEIGHT_DRAM_ADDR_SIZE, config.ACC_ADDR_SIZE, bitwidth, 
        config.INSTRUCTION_WIDTH, config.IMEM_ADDR_SIZE, 
        config.HAZARD_DETECTION)


    # Run Simulation
    sim_trace = SimulationTrace()
    sim = FastSimulation(tracer=sim_trace, memory_value_map={ IMem : { a : v for a,v in enumerate(instrs)} })

    din = {
        weights_dram_in : 0,
        weights_dram_valid : 0,
        hostmem_rdata : 0,
    }

    cycle = 0
    chunkaddr = nchunks
    sim.step(din)
    i = 0
    while True:
        i += 1
        # Halt signal
        if sim.inspect(halt):
            break

        d = din.copy()

        # Check if we're doing a Read Weights
        if chunkaddr < nchunks:
            # print("Sending weights from chunk {}: {}".format(chunkaddr, getchunkfromtile(weighttile, chunkaddr)))
            # print(getchunkfromtile(weighttile, chunkaddr))
            # print(weighttile)
            d[weights_dram_in] = getchunkfromtile(weighttile, chunkaddr)
            d[weights_dram_valid] = 1
            chunkaddr += 1

        # Read host memory signal
        if sim.inspect(hostmem_re): # or sim.inspect(whm_src):
            # print("Reading host memory")
            raddr = sim.inspect(hostmem_raddr)
            # print("Read Host Memory: addr {}".format(raddr))
            if raddr in hostmem: #this causes a pre-mature read of hostmem[end+1] after an RHM read from [start:end]. only lasts for one cycle and doesn't seem to affect anything else
                d[hostmem_rdata] = hostmem[raddr]

        # Write host memory signal
        if sim.inspect(hostmem_we):
            # print("Writing host memory")
            # print("hostmem_waddr = ", sim.inspect(hostmem_waddr))
            # print("hostmem_wdata = ", sim.inspect(hostmem_wdata))
            # print("wdata = ", sim.inspect('wdata'))
            waddr = sim.inspect(hostmem_waddr)
            wdata = sim.inspect(hostmem_wdata)
            hostmem[waddr] = wdata

        # print(f"cycle {cycle}: hostmem[0] = {hostmem[0]}")

        # Read weights memory signal
        if sim.inspect(weights_dram_read):
            # print("Reading weights memory")
            weightaddr = sim.inspect(weights_dram_raddr)
            weighttile = weightsmem[weightaddr]
            chunkaddr = 0
            # print("Read Weights: addr {}".format(weightaddr))
            #print(weighttile)
        
        # print(d)
        
        # sim_trace.print_trace
        # print(f"cycle = {cycle}, pc = {sim.inspect('tpu_pc')}")
        # print(f"mma_in_data_width_0_0 = {sim.inspect('mma_in_matrix_size_0_0')}")
        # print(f"mma_data_width_temp = {sim.inspect('mma_data_width_temp')}")
        # print(f"data_width_temp = {sim.inspect('data_width_temp')}")
        # print(f"act_acc_mems_wv_0 = {sim.inspect('act_acc_mems_wv_0')}")
        # print(f"UBuffer@{cycle}:")
        ub = sim.inspect_mem(UBuffer)
        # for k in sorted(ub.keys()):
        #     print(f"\t{k}: {make_vec_2(ub[k], bitwidth, matsize)}")

        # print(f"AccMems@{cycle}:")
        max_addrs = 0
        for i in range(len(acc_mems)):
            # print("keys = ", sim.inspect_mem(acc_mems[i]).keys())
            max_addrs = max(max_addrs, max(sim.inspect_mem(acc_mems[i]).keys(), default=0))
        # print(max_addrs)
        amems = np.zeros([max_addrs+1, len(acc_mems)+1])
        for i in range(len(acc_mems)):
            ami = sim.inspect_mem(acc_mems[i])
            for k in sorted(ami.keys()):
                amems[k][i+1] = ami[k]
        np.set_printoptions(linewidth=np.inf)
        # print(f"mmu_advance_fifo = {sim.inspect('mmu_advance_fifo')}")

        # for i in range(MATSIZE):
        #     print(f"AccMems[i][start_addr_reg] = {sim.inspect(f'act_acc_mems_at_start_addr_reg_{i}')}")
        for i in range(amems.shape[0]):
            amems[i][0] = i
        # print(amems.astype(int))
        # print("\n\n")
        sim.step(d)
        cycle += 1

    # print("\n\n")
    print("Simulation terminated at cycle {}".format(cycle))

    os.makedirs(output_folder, exist_ok=True)

    if output_trace:
        with open(f'{output_folder}/trace.pkl', 'wb') as file:
            pickle.dump(sim_trace, file)

    hostmem_np = hostmem_to_np(hostmem, bitwidth, matsize)
    weightsmem_np = weightsmem_to_np(weightsmem, bitwidth, matsize)
    ubuffer_np = ubuffer_to_np(sim, UBuffer, bitwidth, matsize, row_count=0)
    wqueue_np = wqueue_to_np(sim, buf4, buf3, buf2, buf1, bitwidth, matsize)
    accmems_np = accmem_to_np(sim, acc_mems, matsize, row_count=0)

    np.savez_compressed(f"{output_folder}/runtpu", hm=hostmem_np, 
                        wm=weightsmem_np, ub=ubuffer_np, wq=wqueue_np, 
                        acc=accmems_np)
    return hostmem_np, weightsmem_np, ubuffer_np, wqueue_np, accmems_np


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Run the PyRTL spec for the TPU on the indicated program.")
    parser.add_argument("prog", metavar="program.bin", help="A valid binary program for OpenTPU.")
    parser.add_argument("hostmem", metavar="HostMemoryArray", help="A file containing a numpy array containing the initial contents of host memory. Each row represents one vector.")
    parser.add_argument("weightsmem", metavar="WeightsMemoryArray", help="A file containing a numpy array containing the contents of the weights memroy. Each row represents one tile (the first row corresponds to the top row of the weights matrix).")
    parser.add_argument("-b", "--bitwidth", type=int, default=32, help="The bitwidth of the data.")
    parser.add_argument("-m", "--matsize", type=int, default=8, help="The size of the matrix.")
    parser.add_argument("-f", "--folder", type=str, default=None, help="The output folder path.")
    args = parser.parse_args()

    if not args.folder:
        args.folder = f'{datetime.now().strftime("%Y-%m-%d_%H:%M:%S")}_{args.bitwidth}b_{args.matsize}m'

    hm, wm, ub, fq, acc = runtpu(args.prog, args.hostmem, args.weightsmem, 
                                 args.bitwidth, args.matsize, args.folder, 
                                 output_trace=True)

    print_mems(hm, wm, ub, fq, acc, args.matsize)
