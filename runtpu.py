import pickle
from pyrtl import *
import argparse
import numpy as np

#set_debug_mode()

from tpu import *
import config

import sys

parser = argparse.ArgumentParser(description="Run the PyRTL spec for the TPU on the indicated program.")
parser.add_argument("prog", metavar="program.bin", help="A valid binary program for OpenTPU.")
parser.add_argument("hostmem", metavar="HostMemoryArray", help="A file containing a numpy array containing the initial contents of host memory. Each row represents one vector.")
parser.add_argument("weightsmem", metavar="WeightsMemoryArray", help="A file containing a numpy array containing the contents of the weights memroy. Each row represents one tile (the first row corresponds to the top row of the weights matrix).")

args = parser.parse_args()
    

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

def concat_vec(vec, bits=8):
    t = 0
    mask = int('1'*bits, 2)
    for x in reversed(vec):
        t = (t<<bits) | (int(x) & mask)
    print(vec, t)
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

def print_mem(mem):
    ks = sorted(mem.keys())
    for a in ks:
        print(a, make_vec(mem[a], DWIDTH))

def print_weight_mem(mem, bits=8, size=8):
    ks = sorted(mem.keys())
    mask = int('1'*(size*bits), 2)
    vecs = []
    for a in ks:
        vec = []
        tile = mem[a]
        while tile > 0:
            vec.append(make_vec(tile & mask, DWIDTH))
            tile = tile >> (bits*size) ###hmmm
        if vec != []:
            vecs.append(vec)
    for a, vec in enumerate(vecs):
        print(a, list(reversed(vec)))
        
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
hostmem = { a : concat_vec(vec, DWIDTH) for a,vec in enumerate(flat_host) }
# print("Host memory start:")
# print(hostmem)
# print_mem(hostmem)

weightsarray = np.load(args.weightsmem)
print("Weightsarray")
print(weightsarray)
print(weightsarray.shape)
size = weightsarray.shape[-1]
weight_shape = weightsarray.shape
if len(weight_shape) == 3:
    weightsmem = { a : concat_tile(tile, DWIDTH) for a,tile in enumerate(weightsarray) }
if len(weight_shape) == 2:
    weightsmem = np.zeros(())
#weightsmem = { a : concat_vec(vec, DWIDTH) for a,vec in enumerate(weightsarray) }
print("Weight memory:")
print_weight_mem(weightsmem, size=size, bits=DWIDTH)
print(weightsmem)

'''
Left-most element of each vector should be left-most in memory: use concat_list for each vector

For weights mem, first vector goes last; hardware already handles this by iterating from back to front over the tile.
The first vector should be at the "front" of the tile.

For host mem, each vector goes at one address. First vector at address 0.
'''

tilesize = config.MATSIZE * config.MATSIZE  # number of weights in a tile
nchunks = max(tilesize / 64, 1)  # Number of DRAM transfers needed from Weight DRAM for one tile
print(f"nchunks = {nchunks}")
chunkmask = pow(2,64*DWIDTH)-1

def getchunkfromtile(tile, chunkn):
    #print("Get chunk: ", chunkn, nchunks, chunkmask, tile)
    #print((tile >> ((nchunks - chunkn - 1)*64*8)) & chunkmask)
    if chunkn >= nchunks:
        raise Exception("Reading more weights than are present in one tile?")
    return (tile >> int(((nchunks - chunkn - 1))*64*DWIDTH)) & chunkmask


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
        print("Sending weights from chunk {}: {}".format(chunkaddr, getchunkfromtile(weighttile, chunkaddr)))
        print(getchunkfromtile(weighttile, chunkaddr))
        print(weighttile)
        d[weights_dram_in] = getchunkfromtile(weighttile, chunkaddr)
        d[weights_dram_valid] = 1
        chunkaddr += 1

    # Read host memory signal
    if sim.inspect(hostmem_re):
        print("Reading host memory")
        raddr = sim.inspect(hostmem_raddr)
        if raddr in hostmem: #this causes a pre-mature read of hostmem[end+1] after an RHM read from [start:end]. only lasts for one cycle and doesn't seem to affect anything else
            d[hostmem_rdata] = hostmem[raddr]

    # Write host memory signal
    if sim.inspect(hostmem_we):
        print("Writing host memory")
        waddr = sim.inspect(hostmem_waddr)
        wdata = sim.inspect(hostmem_wdata)
        hostmem[waddr] = wdata

    # Read weights memory signal
    if sim.inspect(weights_dram_read):
        print("Reading weights memory")
        weightaddr = sim.inspect(weights_dram_raddr)
        weighttile = weightsmem[weightaddr]
        chunkaddr = 0
        print("Read Weights: addr {}".format(weightaddr))
        #print(weighttile)
    
    # print(d)
    
    # sim_trace.print_trace
    print(f"cycle = {cycle}, pc = {sim.inspect('tpu_pc')}")
    # print(f"mma_in_data_width_0_0 = {sim.inspect('mma_in_matrix_size_0_0')}")
    # print(f"mma_data_width_temp = {sim.inspect('mma_data_width_temp')}")
    # print(f"data_width_temp = {sim.inspect('data_width_temp')}")
    # print(f"act_acc_mems_wv_0 = {sim.inspect('act_acc_mems_wv_0')}")
    # print(f"UBuffer@{cycle}: {sim.inspect_mem(UBuffer)}")
    # print(f"AccMems@{cycle}:")
    # for i in range(len(acc_mems)):
    #     print(f"\t{i}: {sim.inspect_mem(acc_mems[i])}")
    # print()
    sim.step(d)
    cycle += 1

print("\n\n")
print("Simulation terminated at cycle {}".format(cycle))
print("Final Host memory:")
print_mem(hostmem)


with open(f'pickled_{DWIDTH}_{MATSIZE}x{MATSIZE}.pkl', 'wb') as file:
    pickle.dump(sim_trace, file)

# sim_trace.render_trace()
# with open("trace.vcd", 'w') as f:
#     sim_trace.print_vcd(f)
# with open("trace.txt", 'w') as f:
#     sim_trace.print_trace(f, compact=True)

# print('ubuffer', sim.inspect_mem(UBuffer))
# for (i, mem) in enumerate(acc_mems):
#     print(f'acc_mem[{i}]', sim.inspect_mem(mem))
