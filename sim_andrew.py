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
        if not args.raw:
            pass
            # assert self.weight_memory.dtype == np.int8, 'DRAM weight mem is not 8-bit ints'
            # assert self.host_memory.dtype == np.int8, 'Hostmem not 8-bit ints'
        self.unified_buffer = (np.zeros((96000, WIDTH), dtype=np.float32) if args.raw else
            np.zeros((96000, WIDTH), dtype=np.int32))
        self.accumulator = (np.zeros((4000, WIDTH), dtype=np.float32) if args.raw else
            np.zeros((4000, WIDTH), dtype=np.int32))
        self.weight_fifo = deque()
        
        self.pc = 0

        self.rw_count = 0
        self.hm_count = 0
        self.mmc_count = 0
        self.act_count = 0
        self.prev_rw = None
        self.reload_count = 0

    def run(self):
        # load program and execute instructions
        instructions = self.decode()
        opcodes, operands = instructions[0], instructions[1]
        
        # use self.pc to select next instruction, starting from 0, and finishing when halt is reached
        while True:
            # print(f'operands = {operands[self.pc]}')
            if opcodes[self.pc] in ['RHM', 'WHM', 'RW']:
                self.memops(opcodes[self.pc], *operands[self.pc])
                if self.pc == 1:
                    print("===Start Host Memory===")
                    print(self.host_memory.astype('int32')[:10])
            elif opcodes[self.pc] == 'MMC':
                self.matrix_multiply_convolve(*operands[self.pc])
                self.mmc_count += 1
            elif opcodes[self.pc] == 'ACT':
                self.act_count += 1
                self.act(*operands[self.pc])
            elif opcodes[self.pc] == 'SYNC':
                self.pc += 1
            elif opcodes[self.pc] == 'NOP':
                self.pc += 1
            elif opcodes[self.pc] == 'HLT':
                # print('H A L T')
                break
            else:
                raise Exception('WAT (╯°□°）╯︵ ┻━┻')

        # all done, exit
        savepath = 'sim32.npy' if args.raw else 'sim8.npy'
        np.save(savepath, self.host_memory)
        print("===Final Host Memory===")
        print(self.host_memory.astype('int32')[:10])
        self.program.close()

        print("MMC Count: {}".format(self.mmc_count))
        print("HM Count: {}".format(self.hm_count))
        print("ACT Count: {}".format(self.act_count))
        print("RW Count: {}".format(self.rw_count))
        print("RW Reloads: {}".format(self.reload_count))


        # print("""ALL DONE!
        # (•_•)
        # ( •_•)>⌐■-■
        # (⌐■_■)""")

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
        # print('ACTIVATE!')
        # if self.pc > 80:
        #     breakpoint()

        result = self.accumulator[src:src+length]
        if flag & isa.FUNC_RELU_MASK:
            # print('  RELU!!!!')
            vfunc = np.vectorize(lambda x: 0 * x if x < 0. else x)
        elif flag & isa.FUNC_SIGMOID_MASK:
            # print('  SIGMOID')
            vfunc = np.vectorize(lambda x: int(255./(1.+exp(-x))))
        else:
            vfunc = np.vectorize(lambda x: x)
            #raise Exception('(╯°□°）╯︵ ┻━┻ bad activation function!')

        # print(f'before = {result}')
        result = vfunc(result)
        # print(f'after = {result}')

        # downsample/normalize if needed
        # Don't downsample for gpmatmul
        # if not args.raw:
        #     result = [v & 0x000000FF for v in result]
        # branching/comparison logic
        if result[0][-1] == 1:
            if result[0][-2] == 1:
                self.pc += 1 + result[0][0].astype(np.int32)
            else:
                self.pc += 1 + result[0][1].astype(np.int32)
            return # don't to the UB write when there's a branch
        # equality check
        elif result[0][-1] == 2:
            result[0][-1] = 0
            if result[0][0] == 0:
                result[0][0] = 1
            else:
                result[0][0] = 0
            result[0][1] = 0
            self.pc += 1
        elif result[0][-1] == 3:
            # breakpoint()
            # can do this bitwise in hardware
            result[0][-1] = 0
            if result[0][0] < 0:
                result[0][0] = 1
            else:
                result[0][0] = 0
            self.pc += 1
        elif result[0][-1] == 4:
            self.pc = result[0][1]
            return
        else:
            self.pc += 1
        self.unified_buffer[dest:dest+length] = result

    def memops(self, opcode, src_addr, dest_addr, length, flag):
        # print('Memory xfer! host: {} unified buffer: {}: length: {} (FLAGS? {})'.format(
        #     src_addr, dest_addr, length, flag
        # ))

        if opcode == 'RHM':
            self.hm_count += 1
            # print('  read host memory to unified buffer')
            read_data = np.zeros((1, WIDTH))
            if flag & isa.SWITCH_MASK:
                addr = self.unified_buffer[-1][0]
                vec_addr = addr // 8
                column = addr % 8
                if length == 0:
                    read_data[0][0] = self.host_memory[vec_addr][column]
                    self.unified_buffer[dest_addr] = read_data
                else:
                    # for a vector load, ignore the column component and start load from the vector pointed to
                    # ...seems possibly problematic lol
                    self.unified_buffer[dest_addr:dest_addr + length] = self.host_memory[vec_addr:vec_addr + length]
            elif flag & isa.CONV_MASK:
                read_data[0][1] = self.pc + 2
                read_data[0][-1] = 4
                self.unified_buffer[dest_addr] = read_data
            else:
                self.unified_buffer[dest_addr:dest_addr + length] = self.host_memory[src_addr:src_addr + length]
        elif opcode == 'WHM':
            self.hm_count += 1
            # print('  write unified buffer to host memory')
            # asm format dest, src, len
            if flag & isa.SWITCH_MASK:
                # breakpoint()
                addr = self.unified_buffer[-1][0]
                vec_addr = addr // 8
                column = addr % 8
                if length == 0:
                    self.host_memory[vec_addr][column] = self.unified_buffer[src_addr][0]
                else:
                    try:
                        self.host_memory[vec_addr:vec_addr + length] = self.unified_buffer[src_addr:src_addr + length]
                    except ValueError:
                        breakpoint()
            else:
                self.host_memory[dest_addr:dest_addr + length] = self.unified_buffer[src_addr:src_addr + length]
        elif opcode == 'RW':
            if src_addr != self.prev_rw:
                self.reload_count += 1
                self.prev_rw = src_addr

            self.rw_count += 1
            # print('  read weights from DRAM into MMU')
            self.weight_fifo.append(self.weight_memory[src_addr])
        else:
            raise Exception('WAT (╯°□°）╯︵ ┻━┻')
        
        self.pc += 1

    def matrix_multiply_convolve(self, ub_addr, accum_addr, size, flags):
        # print('Matrix things....')
        # print('  UB@{} + {} -> MMU -> accumulator@{} + {}'.format(
        #     ub_addr, size, accum_addr, size
        # ))

        inp = self.unified_buffer[ub_addr: ub_addr + size]
        # print('MMC input shape: {}'.format(inp.shape))
        weight_mat = self.weight_fifo.popleft()
        if not args.raw:
            inp = inp.astype(np.int32)
            weight_mat = weight_mat.astype(np.int32)
        # print('MMC matrix: \n{}'.format(inp))
        # print('MMC weight: \n{}'.format(weight_mat))
        out = np.matmul(inp, weight_mat)
        # print('MMC output shape: {}'.format(out.shape))
        # print('MMC output: \n{}'.format(out))
        overwrite = isa.OVERWRITE_MASK & flags
        if overwrite:
            self.accumulator[accum_addr:accum_addr + size] = out
        else:
            self.accumulator[accum_addr:accum_addr + size] += out
        # print(f'Accumulator[{accum_addr}] = {self.accumulator[accum_addr: accum_addr + size]}')

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
