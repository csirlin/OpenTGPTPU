# coding=utf-8
import argparse
import sys
import numpy as np
from collections import deque
from math import exp

import isa
from config import MATSIZE as WIDTH

args = None
# width of the tile
#WIDTH = 16


class TPUSim(object):
    def __init__(self, program_filename, dram_filename, hostmem_filename):
        # TODO: switch b/w 32-bit float vs int
        self.program = open(program_filename, 'rb')
        self.weight_memory = np.load(dram_filename)
        self.host_memory = np.load(hostmem_filename)
        # if not args.raw:
        #     assert self.weight_memory.dtype == np.int8, 'DRAM weight mem is not 8-bit ints'
        #     assert self.host_memory.dtype == np.int8, 'Hostmem not 8-bit ints'
        self.unified_buffer = (np.zeros((96000, WIDTH), dtype=np.float32) if args.raw else
            np.zeros((96000, WIDTH), dtype=np.int32)) # update to match the bitwidth specified in config.py
        self.accumulator = (np.zeros((4000, WIDTH), dtype=np.float32) if args.raw else
            np.zeros((4000, WIDTH), dtype=np.int32))
        self.weight_fifo = deque()
        
        self.pc = 0

    def run(self):
        # load program and execute instructions
        instructions = self.decode()
        opcodes, operands = instructions[0], instructions[1]
        # print(f"Instructions:")
        # if (len(instructions[0]) != len(instructions[1])):
        #     raise ValueError("Mismatched instruction and operand lengths.")
        # for i in range(len(instructions[0])):
        #     print(f"{i}: {opcodes[i]}, {operands[i]}")
        
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
        savepath = 'sim32.npy' if args.raw else 'sim8.npy'
        np.save(savepath, self.host_memory)
        print(f'Final host memory:')
        print(self.host_memory.astype('uint8'))
        self.program.close()

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

        # downsample/normalize if needed
        # if not args.raw:
        #     result = [v & 0x000000FF for v in result]
        
        # new scheme #
        # branching/comparison logic
        if result[0][-1] == 1:
            if result[0][-2] == 1:
                self.pc += 1 + result[0][0].astype(np.int8)
            else:
                self.pc += 1 + result[0][1].astype(np.int8)
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
        elif result[0][-1] == 3:
            # breakpoint()
            result[0][-1] == 0
            if result[0][0] < result[0][1]:
                result[0][0] = 1
            else:
                result[0][0] = 0
            result[0][1] = 0
            self.pc += 1 
        else:
            self.pc += 1
        # end new scheme #

        # # orig scheme #
        # branch if equal weight matrix holds e and p. if result[0][0] == 0 and e == 1, pc += p. else pc += 1
        # print(f"result[0] = {result[0]}")
        # print(f"result[0][-3] = {result[0][-3]}")
        # print(f"branch_eq_vect: enabled = {result[0][-2]}, branch pc diff = {256*result[0][-4] + result[0][-3]}")
        # if (0 > result[0][-2] > 1):
        #     raise ValueError(f"Branch boolean must be 0 or 1. Instead it's {result[0][-2]}.)")
        # if (result[0][-2] == 1 and result[0][0] == 0):
        #     self.pc += (256*result[0][-4] + result[0][-3] + 1).astype(np.int16)
        # else:
        #     self.pc += 1
        # # end orig scheme #        

        self.unified_buffer[dest:dest+length] = result
        # #

    def memops(self, opcode, src_addr, dest_addr, length, flag):
        # print('Memory xfer! from: {} to: {}: length: {} (FLAGS? {})'.format(
        #     src_addr, dest_addr, length, flag
        # ))

        if opcode == 'RHM':
            print(f'RHM: read host memory [{src_addr}:{src_addr + length}], write to unified buffer [{dest_addr}:{dest_addr + length}]. Flags? {flag}')
            print(self.host_memory[src_addr:src_addr + length])
            self.unified_buffer[dest_addr:dest_addr + length] = self.host_memory[src_addr:src_addr + length]
        elif opcode == 'WHM':
            print(f'WHM: read unified buffer [{src_addr}:{src_addr + length}], write to host memory [{dest_addr}:{dest_addr + length}]. Flags? {flag}')
            print(self.unified_buffer[src_addr:src_addr + length])
            
            # extend the host memory if needed
            if (self.host_memory.shape[0] < dest_addr + length):
                self.host_memory.resize((dest_addr + length, WIDTH))
            
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
        # print('MMC input shape: {}'.format(inp.shape))
        weight_mat = self.weight_fifo[0]
        if isa.SWITCH_MASK & flags:  # shouldn't this only happen when using .S?
            self.weight_fifo.popleft()
        if not args.raw:
            inp = inp.astype(np.int32)
            weight_mat = weight_mat.astype(np.int32)
        print('MMC matrix: \n{}'.format(inp))
        print('MMC weight: \n{}'.format(weight_mat))
        out = np.matmul(inp, weight_mat)
        # print('MMC output shape: {}'.format(out.shape))
        print('MMC output: \n{}'.format(out))
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
    parser.add_argument('program', action='store',
                        help='Path to assembly program file.')
    parser.add_argument('host_file', action='store',
                        help='Path to host file.')
    parser.add_argument('dram_file', action='store',
                        help='Path to dram file.')
    parser.add_argument('--raw', action='store_true', default=False,
                        help='Gen sim32.npy instead of sim8.npy.')
    args = parser.parse_args()

if __name__ == '__main__':
    np.set_printoptions(linewidth=150)
    if len(sys.argv) < 4:
        print('Usage:', sys.argv[0], 'PROGRAM_BINARY DRAM_FILE HOST_FILE')
        sys.exit(0)
    
    parse_args()
    tpusim = TPUSim(args.program, args.dram_file, args.host_file)
    tpusim.run()
