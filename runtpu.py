from datetime import datetime
import os
import pickle
from pyrtl import *
import argparse
import numpy as np

#set_debug_mode()

from tpu import tpu
import config


def concat_vec(vec, bits=8):
    t = 0
    mask = int('1'*bits, 2)
    for x in reversed(vec):
        t = (t<<bits) | (int(x) & mask)
    # print(vec, t)
    return t

def concat_tile(tile, bits=8):
    val = 0
    size = len(tile)
    mask = int('1'*bits, 2)
    for row in tile:
        for x in row:
            val = (val<<bits) | (int(x) & mask)
        #print_weight_mem({0:val})
    #return val & (size*size*bits)  # if negative, truncate bits to correct size
    return val

def make_vec(value, bits=8):
    vec = []
    mask = int('1'*bits, 2)
    while value > 0:
        vec.append(value & mask)
        value = value >> bits
    return list(reversed(vec))

def make_vec_2(value, bits=8, size=8):
    vec = []
    mask = int('1'*bits, 2)
    for i in range(size):
        vec.append(value & mask)
        value = value >> bits
    return list(vec)

def print_mem(mem):
    ks = sorted(mem.keys())
    for a in ks:
        print(a, make_vec_2(mem[a], config.DWIDTH, config.MATSIZE))

def print_weight_mem(mem, bits=8, size=8):
    ks = sorted(mem.keys())
    mask = int('1'*(size*bits), 2)
    vecs = []
    for a in ks:
        vec = []
        tile = mem[a]
        while tile > 0:
            vec.append(make_vec(tile & mask, config.DWIDTH))
            tile = tile >> (bits*size) ###hmmm
        if vec != []:
            vecs.append(vec)
    for a, vec in enumerate(vecs):
        print(a, list(reversed(vec)))


def runtpu(args, output_folder_path='test', output_trace=False):
    # Read the program and build an instruction list
    with open(args.prog, 'rb') as f:
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
    hostarray = np.load(args.hostmem)
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
    hostmem = { a : concat_vec(vec, config.DWIDTH) for a,vec in enumerate(flat_host) }
    # print("Host memory start:")
    # print(hostmem)
    # print_mem(hostmem)

    weightsarray = np.load(args.weightsmem)
    # print("Weightsarray")
    # print(weightsarray)
    # print(weightsarray.shape)
    size = weightsarray.shape[-1]
    weight_shape = weightsarray.shape
    if len(weight_shape) == 3:
        weightsmem = { a : concat_tile(tile, config.DWIDTH) for a,tile in enumerate(weightsarray) }
    if len(weight_shape) == 2:
        weightsmem = np.zeros(())
    #weightsmem = { a : concat_vec(vec, DWIDTH) for a,vec in enumerate(weightsarray) }
    # print("Weight memory:")
    # print_weight_mem(weightsmem, size=size, bits=config.DWIDTH)
    # print(weightsmem)

    '''
    Left-most element of each vector should be left-most in memory: use concat_list for each vector

    For weights mem, first vector goes last; hardware already handles this by iterating from back to front over the tile.
    The first vector should be at the "front" of the tile.

    For host mem, each vector goes at one address. First vector at address 0.
    '''
    tilesize = config.MATSIZE * config.MATSIZE  # number of weights in a tile
    nchunks = max(tilesize / 64, 1)  # Number of DRAM transfers needed from Weight DRAM for one tile
    # print(f"nchunks = {nchunks}")
    chunkmask = pow(2,64*config.DWIDTH)-1

    def getchunkfromtile(tile, chunkn):
        #print("Get chunk: ", chunkn, nchunks, chunkmask, tile)
        #print((tile >> ((nchunks - chunkn - 1)*64*8)) & chunkmask)
        if chunkn >= nchunks:
            raise Exception("Reading more weights than are present in one tile?")
        return (tile >> int(((nchunks - chunkn - 1))*64*config.DWIDTH)) & chunkmask

    reset_working_block()
    IMem, UBuffer, weights_dram_in, weights_dram_valid, hostmem_rdata, halt, \
        hostmem_re, hostmem_raddr, hostmem_we, hostmem_waddr, hostmem_wdata, \
        weights_dram_read, weights_dram_raddr, acc_mems, buf4, buf3, buf2, buf1 \
        = tpu(config.MATSIZE, config.HOST_ADDR_SIZE, config.UB_ADDR_SIZE, 
        config.WEIGHT_DRAM_ADDR_SIZE, config.ACC_ADDR_SIZE, config.DWIDTH, 
        config.INSTRUCTION_WIDTH, config.IMEM_ADDR_SIZE)


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
        if sim.inspect(hostmem_re):
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
        #     print(f"\t{k}: {make_vec_2(ub[k], config.DWIDTH, config.MATSIZE)}")

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
    # print("Final Host memory:")
    # print_mem(hostmem)

    os.makedirs(output_folder_path, exist_ok=True)

    if output_trace:
        with open(f'{output_folder_path}/trace.pkl', 'wb') as file:
            pickle.dump(sim_trace, file)

    with open(f'{output_folder_path}/hostmem.pkl', 'wb') as file:
        pickle.dump(hostmem, file)

    # with open(f'{output_folder_path}/ubuffer.pkl', 'wb') as file:
    #     pickle.dump(UBuffer, file)

    # with open(f'{output_folder_path}/accmems.pkl', 'wb') as file:
    #     pickle.dump(acc_mems, file)

    # with open(f'{output_folder_path}/wqueue.pkl', 'wb') as file:
    #     pickle.dump((buf4, buf3, buf2, buf1), file)

    return hostmem #, UBuffer, acc_mems, (buf4, buf3, buf2, buf1)

    # sim_trace.render_trace()
    # with open("trace.vcd", 'w') as f:
    #     sim_trace.print_vcd(f)
    # with open("trace.txt", 'w') as f:
    #     sim_trace.print_trace(f, compact=True)

    # print('ubuffer', sim.inspect_mem(UBuffer))
    # for (i, mem) in enumerate(acc_mems):
    #     print(f'acc_mem[{i}]', sim.inspect_mem(mem))


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Run the PyRTL spec for the TPU on the indicated program.")
    parser.add_argument("prog", metavar="program.bin", help="A valid binary program for OpenTPU.")
    parser.add_argument("hostmem", metavar="HostMemoryArray", help="A file containing a numpy array containing the initial contents of host memory. Each row represents one vector.")
    parser.add_argument("weightsmem", metavar="WeightsMemoryArray", help="A file containing a numpy array containing the contents of the weights memroy. Each row represents one tile (the first row corresponds to the top row of the weights matrix).")
    args = parser.parse_args()

    runtpu(args, name=f'{datetime.now().strftime("%Y-%m-%d_%H:%M:%S")}_{config.DWIDTH}b_{config.MATSIZE}m')
