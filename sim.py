# coding=utf-8
import argparse
import sys
import numpy as np
from collections import deque
from math import exp

import isa

SIGNED_DTYPES = {
    8: np.uint8,
    16: np.uint16,
    32: np.uint32,
    64: np.uint64
}

UNSIGNED_DTYPES = {
    8: np.int8,
    16: np.int16,
    32: np.int32,
    64: np.int64
}

class TPUSim(object):
    def __init__(self, prog: str, hostmem_filename: str, 
                 weightsmem_filename: str, bitwidth: int, matsize: int, 
                 output_folder: str):
        self.program = open(prog, 'rb')
        self.weight_memory = np.load(weightsmem_filename).astype(SIGNED_DTYPES[bitwidth])
        self.host_memory = np.load(hostmem_filename).astype(SIGNED_DTYPES[bitwidth])

        self.unified_buffer = np.zeros(self.host_memory.shape, dtype=SIGNED_DTYPES[bitwidth])
        self.accumulator = np.zeros(self.host_memory.shape, dtype=SIGNED_DTYPES[bitwidth])
        self.weight_fifo = deque()

        self.bitwidth = bitwidth
        self.matsize = matsize
        self.output_folder = output_folder

        self.pc = 0

    def print_mems(self):
        np.set_printoptions(threshold=np.inf, linewidth=300)
        print("Host memory:\n", self.host_memory)
        print("Weight memory:\n", self.weight_memory)
        print("UBuffer:\n", self.unified_buffer)
        print("FIFO Queue:\n", np.array(self.weight_fifo)) # can't believe this just works :O
        print("Accumulators:\n", self.accumulator)

    def get_mems(self):
        return self.host_memory, self.weight_memory, self.unified_buffer, self.weight_fifo, self.accumulator

    def run(self):
        # load program and execute instructions
        instructions = self.decode()
        opcodes, operands = instructions[0], instructions[1]

        if (len(instructions[0]) != len(instructions[1])):
            raise ValueError("Mismatched instruction and operand lengths.")
        
        # use self.pc to select next instruction, starting from 0, and finishing when halt is reached
        while True:
            # print(f'operands = {operands[self.pc]}')
            print(f"PC = {self.pc}")
            if opcodes[self.pc] in ['RHM', 'WHM', 'RW']:
                self.memops(opcodes[self.pc], *operands[self.pc])
            elif opcodes[self.pc] == 'MMC':
                self.matrix_multiply_convolve(*operands[self.pc])
            elif opcodes[self.pc] == 'ACT':
                self.act(*operands[self.pc])
            elif opcodes[self.pc] == 'SYNC':
                self.pc += 1
            elif opcodes[self.pc] == 'NOP':
                self.pc += 1
            elif opcodes[self.pc] == 'HLT':
                print('H A L T')
                break
            else:
                raise Exception('WAT (╯°□°）╯︵ ┻━┻')
            print()

        # all done, exit
        self.program.close()
        np.save(f'{self.output_folder}/sim_hostmem.npy', self.host_memory)
        np.save(f'{self.output_folder}/sim_weightsmem.npy', self.weight_memory)
        np.save(f'{self.output_folder}/sim_ubuffer.npy', self.unified_buffer)
        np.save(f'{self.output_folder}/sim_wqueue.npy', np.array(self.weight_fifo))
        np.save(f'{self.output_folder}/sim_accmems.npy', self.accumulator)

        print("""\nALL DONE!
        (•_•)
        ( •_•)>⌐■-■
        (⌐■_■)""")

    # decode everything at once and return lists
    def decode(self):
        opcode_list = []
        operand_list = []
        current_opcode = ""

        while True:
            bytes = self.program.read(isa.OP_SIZE)
            if not bytes:
                break
            current_opcode = int.from_bytes(bytes, byteorder='big')
            current_opcode = isa.BIN2OPCODE[current_opcode]
            opcode_list.append(current_opcode)
            current_flag = int.from_bytes(self.program.read(isa.FLAGS_SIZE), byteorder='big')
            current_length = int.from_bytes(self.program.read(isa.LEN_SIZE), byteorder='big')
            current_src_addr = int.from_bytes(self.program.read(isa.ADDR_SIZE), byteorder='big')
            current_dest_addr = int.from_bytes(self.program.read(isa.UB_ADDR_SIZE), byteorder='big')
            operand_list.append((current_src_addr, current_dest_addr, current_length, current_flag))

        return opcode_list, operand_list

    # opcodes
    def act(self, src, dest, length, flag):
        print(f'ACT: read ACC[{src}:{src + length}], and write to UB[{dest}:{dest + length}]. Activation function:', end = ' ')

        result = self.accumulator[src:src+length]
        if flag & isa.FUNC_RELU_MASK:
            print('RELU!!!!')
            vfunc = np.vectorize(lambda x: 0 * x if x < 0. else x)
        elif flag & isa.FUNC_SIGMOID_MASK:
            print('SIGMOID')
            vfunc = np.vectorize(lambda x: int(255./(1.+exp(-x))))
        else:
            print('None')
            vfunc = np.vectorize(lambda x: x)
            #raise Exception('(╯°□°）╯︵ ┻━┻ bad activation function!')

        print(f'Before activation:\n{result}')
        result = vfunc(result)
        print(f'After activation:\n{result}')
        
        # branching/comparison logic
        if result[0][-1] == 1:
            if result[0][-2] == 1:
                self.pc += 1 + result[0][0].astype(SIGNED_DTYPES[self.bitwidth])
            else:
                self.pc += 1 + result[0][1].astype(SIGNED_DTYPES[self.bitwidth])
            return # don't to the UB write when there's a branch
        
        # equality check
        elif result[0][-1] == 2:
            result[0][-1] == 0
            if result[0][0] == result[0][1]:
                result[0][0] = 1
            else:
                result[0][0] = 0
            result[0][1] = 0
            self.pc += 1
        
        # less than check
        elif result[0][-1] == 3:
            result[0][-1] == 0
            if result[0][0] < result[0][1]:
                result[0][0] = 1
            else:
                result[0][0] = 0
            result[0][1] = 0
            self.pc += 1 

        # normal activation
        else:
            self.pc += 1      

        # extend the unified buffer if needed
        if (self.unified_buffer.shape[0] < dest + length):
            self.unified_buffer.resize((dest + length, self.matsize))
        self.unified_buffer[dest:dest+length] = result

    def memops(self, opcode, src_addr, dest_addr, length, flag):
        if opcode == 'RHM':
            print(f'RHM: read host memory [{src_addr}:{src_addr + length}], write to unified buffer [{dest_addr}:{dest_addr + length}]. Flags? {flag}')
            print(self.host_memory[src_addr:src_addr + length])

            # extend the unified buffer if needed
            if (self.unified_buffer.shape[0] < dest_addr + length):
                self.unified_buffer.resize((dest_addr + length, self.matsize))
            self.unified_buffer[dest_addr:dest_addr + length] = self.host_memory[src_addr:src_addr + length]

        elif opcode == 'WHM':
            print(f'WHM: read unified buffer [{src_addr}:{src_addr + length}], write to host memory [{dest_addr}:{dest_addr + length}]. Flags? {flag}')
            print(self.unified_buffer[src_addr:src_addr + length])
            
            # extend the host memory if needed
            if (self.host_memory.shape[0] < dest_addr + length):
                self.host_memory.resize((dest_addr + length, self.matsize))
            self.host_memory[dest_addr:dest_addr + length] = self.unified_buffer[src_addr:src_addr + length]

        elif opcode == 'RW':
            print(f'RW {src_addr}: read weight matrix {src_addr} into weight FIFO')
            print(self.weight_memory[src_addr])
            self.weight_fifo.append(self.weight_memory[src_addr])

        else:
            raise Exception('WAT (╯°□°）╯︵ ┻━┻')
        
        self.pc += 1

    def matrix_multiply_convolve(self, ub_addr, accum_addr, size, flags):
        print(f'MMC: multiply UB[{ub_addr}:{ub_addr + size}] with a weight, store in ACC[{accum_addr}:{accum_addr + size}]')

        inp = self.unified_buffer[ub_addr: ub_addr + size]
        weight_mat = self.weight_fifo[0]
        
        if isa.SWITCH_MASK & flags:
            self.weight_fifo.popleft()

        print('MMC matrix: \n{}'.format(inp))
        print('MMC weight: \n{}'.format(weight_mat))

        out = np.matmul(inp, weight_mat)

        print('MMC output: \n{}'.format(out))

        # extend the accumulator if needed
        if (self.accumulator.shape[0] < accum_addr + size):
            self.accumulator.resize((accum_addr + size, self.matsize))

        overwrite = isa.OVERWRITE_MASK & flags
        if overwrite:
            print(f'Overwriting ACC[{accum_addr}:{accum_addr + size}]')
            self.accumulator[accum_addr:accum_addr + size] = out
        else:
            print(f'Accumulating with ACC[{accum_addr}:{accum_addr + size}]')
            print(f'{self.accumulator[accum_addr: accum_addr + size]}')
            self.accumulator[accum_addr:accum_addr + size] += out
        
        print(f'After MMC + ACC: \n{self.accumulator[accum_addr: accum_addr + size]}')

        self.pc += 1

def parse_args():
    global args

    parser = argparse.ArgumentParser()
    parser.add_argument('prog', action='store', help='Path to assembly program file.')
    parser.add_argument('hostmem', action='store', help='Path to host file.')
    parser.add_argument('weightsmem', action='store', help='Path to dram file.')
    parser.add_argument('-b', "--bitwidth", type=int, default=32, help="The bitwidth of the data.")
    parser.add_argument('-m', "--matsize", type=int, default=8, help="The size of the matrix.")
    parser.add_argument('-f', "--folder", type=str, default=None, help="The output folder path.")
    args = parser.parse_args()

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print('Usage:', sys.argv[0], 'PROGRAM_BINARY DRAM_FILE HOST_FILE')
        sys.exit(0)
    parse_args()

    tpusim = TPUSim(args.prog, args.hostmem, args.weightsmem, args.bitwidth,
                    args.matsize, args.folder)
    tpusim.run()
    tpusim.print_mems()
