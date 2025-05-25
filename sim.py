# coding=utf-8
import argparse
from datetime import datetime
import os
import sys
import numpy as np
from collections import deque
from math import exp
import utils
import config
import isa

SIGNED_DTYPES = {
    8: np.int8,
    16: np.int16,
    32: np.int32,
    64: np.int64
}

UNSIGNED_DTYPES = {
    8: np.uint8,
    16: np.uint16,
    32: np.uint32,
    64: np.uint64
}

class TPUSim(object):
    def __init__(self, prog: str, hostmem_filename: str, 
                 weightsmem_filename: str, bitwidth: int, matsize: int, 
                 output_folder: str):
        self.program = open(prog, 'rb')
        self.weight_memory = np.load(weightsmem_filename).astype(UNSIGNED_DTYPES[bitwidth])
        self.host_memory = np.load(hostmem_filename).astype(UNSIGNED_DTYPES[bitwidth])

        self.unified_buffer = np.zeros((0, matsize), dtype=UNSIGNED_DTYPES[bitwidth])
        self.accumulator = np.zeros((0, matsize), dtype=UNSIGNED_DTYPES[bitwidth])
        self.weight_fifo = deque()

        self.bitwidth = bitwidth
        self.matsize = matsize
        self.output_folder = output_folder

        self.pc = 0
        self.pc_history = []

        self.rw_count = 0
        self.hm_count = 0
        self.mmc_count = 0
        self.act_count = 0
        self.prev_rw = None
        self.reload_count = 0

    def get_mems(self):
        return self.host_memory, self.weight_memory, self.unified_buffer, \
               self.fifo_to_np(), self.accumulator

    def fifo_to_np(self):
        return np.array(self.weight_fifo)\
                 .reshape((len(self.weight_fifo), self.matsize, self.matsize))

    # resize the slice to fit shape. slice.shape and shape will always have
    # the same width, and slice.shape's height will be less than or equal to 
    # shape's height. if less, the extra rows will be filled with 0s. this lets
    # memories get read beyond their current address without creating new rows,
    # while writing non-existant 0-rows to the write memeory
    def pad_zeros(self, slice, shape):
        if slice.shape[0] < shape[0]:
            print(f"padded with {shape[0] - slice.shape[0]} 0-rows")
        res = np.zeros(shape, dtype=UNSIGNED_DTYPES[self.bitwidth])
        res[:slice.shape[0]] = slice
        return res

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
            self.pc_history.append(self.pc)
            if opcodes[self.pc] in ['RHM', 'WHM', 'RW']:
                self.memops(opcodes[self.pc], *operands[self.pc])
            elif opcodes[self.pc] == 'MMC':
                self.matrix_multiply_convolve(*operands[self.pc])
                self.mmc_count += 1
            elif opcodes[self.pc] == 'ACT':
                self.act(*operands[self.pc])
                self.act_count += 1
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

        print("MMC Count: {}".format(self.mmc_count))
        print("HM Count: {}".format(self.hm_count))
        print("ACT Count: {}".format(self.act_count))
        print("RW Count: {}".format(self.rw_count))
        print("RW Reloads: {}".format(self.reload_count))

        os.makedirs(self.output_folder, exist_ok=True)
        np.savez_compressed(f"{self.output_folder}/sim", hm=self.host_memory, 
                            wm=self.weight_memory, ub=self.unified_buffer, 
                            wq=self.fifo_to_np(), acc=self.accumulator)

        print("PC history:\n", self.pc_history)

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

        # extend the accumulator if needed
        result = self.pad_zeros(self.accumulator[src:src+length], (length, self.matsize))
        if flag & isa.FUNC_RELU_MASK:
            print('RELU!!!!')
            vfunc = np.vectorize(lambda x: 0 * x if x < 0. else x)
        elif flag & isa.FUNC_SIGMOID_MASK:
            print('SIGMOID')
            vfunc = np.vectorize(lambda x: int(255./(1.+exp(-x))))
        else:
            # print('None')
            vfunc = np.vectorize(lambda x: x)
            #raise Exception('(╯°□°）╯︵ ┻━┻ bad activation function!')

        print(f'Before activation:\n{result}')
        result = vfunc(result)
        print(f'After activation:\n{result}')
        
        # branching/comparison logic
        if result[0][-1] == 1:
            if result[0][-2] == 1:
                print(f"Branch from {self.pc} to {self.pc + 1 + result[0][0]}. No write to UB.")
                self.pc = int(self.pc + 1 + result[0][0]) % 2**config.IMEM_ADDR_SIZE
            else:
                print(f"Branch from {self.pc} to {self.pc + 1 + result[0][1]}. No write to UB.")
                self.pc = int(self.pc + 1 + result[0][1]) % 2**config.IMEM_ADDR_SIZE
            return # don't to the UB write when there's a branch
        
        # equality check
        elif result[0][-1] == 2:
            result[0][-1] = 0
            if result[0][0] == 0:
                print(f"Equality check, evaluates to True.")
                result[0][0] = 1
            else:
                print(f"Equality check, evaluates to False.")
                result[0][0] = 0
            result[0][1] = 0
            self.pc += 1
        
        # less than check
        elif result[0][-1] == 3:
            result[0][-1] = 0
            if result[0][0] < 0:
                print(f"Less than check, evaluates to True ({result[0][0]} < 0).")
                result[0][0] = 1
            else:
                print(f"Less than check, evaluates to False ({result[0][0]} !< 0).")
                result[0][0] = 0
            self.pc += 1
        
        # unconditional jump
        elif result[0][-1] == 4:
            print(f"Unconditional jump from {self.pc} to {result[0][1]}. No write to UB.")
            self.pc = int(result[0][1])
            return

        # normal activation
        else:
            print(f"Normal activation.")
            self.pc += 1      

        print("After branch/comparison/jump:")
        print(result)

        # extend the unified buffer if needed
        if (self.unified_buffer.shape[0] < dest + length):
            self.unified_buffer.resize((dest + length, self.matsize))
        self.unified_buffer[dest:dest+length] = result

    def memops(self, opcode, src_addr, dest_addr, length, flag):
        if opcode == 'RHM':
            self.hm_count += 1
            read_data = np.zeros((1, self.matsize))

            if flag & isa.SWITCH_MASK:
                # extending UB to 2^UB_SIZE-1 could cause mismatch between sim 
                # and runtpu but hard to fix. fortunately it's hard to see a
                # scenario where this would get read from but never written to
                if (self.unified_buffer.shape[0] < 2**config.UB_ADDR_SIZE): 
                    self.unified_buffer.resize((2**config.UB_ADDR_SIZE, self.matsize))
                addr = self.unified_buffer[2**config.UB_ADDR_SIZE-1][0]
                vec_addr = addr // self.matsize
                column = addr % self.matsize
                
                if length == 0:
                    print(f"RHM vec cell: read host memory [{vec_addr}][{column}] and pad with 0s, write to unified buffer [{dest_addr}]. Buffer addr is {addr} -> [{vec_addr}][{column}]. Flags? {flag}")
                    read_data[0][0] = self.pad_zeros(self.host_memory[vec_addr:vec_addr+1], (1, self.matsize))[0][column]
                    if (self.unified_buffer.shape[0] < dest_addr + 1):
                        self.unified_buffer.resize((dest_addr + 1, self.matsize))
                    print(read_data)
                    self.unified_buffer[dest_addr] = read_data
                
                else:
                    print(f"RHM vec matrix: read host memory [{vec_addr}:{vec_addr + length}], write to unified buffer [{dest_addr}:{dest_addr + length}]. Buffer addr is {addr} -> [{vec_addr}][{column}]. Flags? {flag}")
                    if (self.unified_buffer.shape[0] < dest_addr + length):
                        self.unified_buffer.resize((dest_addr + length, self.matsize))
                    print(self.host_memory[vec_addr:vec_addr + length])
                    res = self.pad_zeros(self.host_memory[vec_addr:vec_addr+length], (length, self.matsize))
                    print(res)
                    self.unified_buffer[dest_addr:dest_addr + length] = res

            elif flag & isa.CONV_MASK:
                print(f"RHM pc return: create curent pc vector, write to unified buffer [{dest_addr}]. Flags? {flag}")
                read_data[0][1] = self.pc + 2
                read_data[0][-1] = 4
                print(read_data)
                if (self.unified_buffer.shape[0] < dest_addr + 1):
                    self.unified_buffer.resize((dest_addr + 1, self.matsize))
                self.unified_buffer[dest_addr] = read_data
            
            else:
                print(f"RHM standard matrix: read host memory [{src_addr}:{src_addr + length}], write to unified buffer [{dest_addr}:{dest_addr + length}]. Flags? {flag}")
                if (self.unified_buffer.shape[0] < dest_addr + length):
                    self.unified_buffer.resize((dest_addr + length, self.matsize))
                res = self.pad_zeros(self.host_memory[src_addr:src_addr+length], (length, self.matsize))
                print(res)
                self.unified_buffer[dest_addr:dest_addr + length] = res

        elif opcode == 'WHM':
            self.hm_count += 1
            
            if flag & isa.SWITCH_MASK:
                if (self.unified_buffer.shape[0] < 2**config.UB_ADDR_SIZE):
                    self.unified_buffer.resize((2**config.UB_ADDR_SIZE, self.matsize))
                addr = self.unified_buffer[2**config.UB_ADDR_SIZE-1][0]
                vec_addr = addr // self.matsize
                column = addr % self.matsize
                
                if length == 0:
                    print(f"WHM vec cell: read unified buffer [{src_addr}][0], write to host memory [{vec_addr}][{column}]. Buffer addr is {addr} -> [{vec_addr}][{column}]. Flags? {flag}")
                    if (self.host_memory.shape[0] < vec_addr + 1):
                        self.host_memory.resize((vec_addr + 1, self.matsize))
                    res = self.pad_zeros(self.unified_buffer[src_addr:src_addr+1], (1, self.matsize))
                    print(f"UB[{src_addr}]: {res}")
                    print(f"HM[{vec_addr}] before: {self.host_memory[vec_addr]}")
                    self.host_memory[vec_addr][column] = res[0][0]
                    print(f"HM[{vec_addr}]  after: {self.host_memory[vec_addr]}")
                
                else:
                    print(f"WHM vec matrix: read unified buffer [{src_addr}:{src_addr + length}], write to host memory [{vec_addr}:{vec_addr + length}]. Buffer addr is {addr} -> [{vec_addr}][{column}]. Flags? {flag}")
                    if (self.host_memory.shape[0] < vec_addr + length):
                        self.host_memory.resize((vec_addr + length, self.matsize))
                    res = self.pad_zeros(self.unified_buffer[src_addr:src_addr+length], (length, self.matsize))
                    print(res)
                    self.host_memory[vec_addr:vec_addr + length] = res
            
            else:
                print(f"WHM standard matrix: read unified buffer [{src_addr}:{src_addr + length}], write to host memory [{dest_addr}:{dest_addr + length}]. Flags? {flag}")
                if (self.host_memory.shape[0] < dest_addr + length):
                    self.host_memory.resize((dest_addr + length, self.matsize))
                res = self.pad_zeros(self.unified_buffer[src_addr:src_addr+length], (length, self.matsize))
                print(res)
                self.host_memory[dest_addr:dest_addr + length] = res
        
        elif opcode == 'RW':
            print(f'RW {src_addr}: read weight matrix {src_addr} into weight FIFO')
            print(self.weight_memory[src_addr])
            if src_addr != self.prev_rw:
                self.reload_count += 1
                self.prev_rw = src_addr

            self.rw_count += 1
            self.weight_fifo.append(self.weight_memory[src_addr])

        else:
            raise Exception('WAT (╯°□°）╯︵ ┻━┻')
        
        self.pc += 1

    def matrix_multiply_convolve(self, ub_addr, accum_addr, size, flags):
        print(f'MMC: multiply UB[{ub_addr}:{ub_addr + size}] with a weight, store in ACC[{accum_addr}:{accum_addr + size}]')

        inp = self.pad_zeros(self.unified_buffer[ub_addr:ub_addr + size], (size, self.matsize))
        weight_mat = self.weight_fifo[0]
        
        if isa.SWITCH_MASK & flags:
            self.weight_fifo.popleft()

        print('MMC matrix: \n{}'.format(inp))
        print('MMC weight: \n{}'.format(weight_mat))

        out = np.matmul(inp.astype(SIGNED_DTYPES[self.bitwidth]), 
                        weight_mat.astype(SIGNED_DTYPES[self.bitwidth]))\
                        .astype(UNSIGNED_DTYPES[self.bitwidth])

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
        
        print(f'After MMC + ACC: \n{self.accumulator[accum_addr:accum_addr + size]}')

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

    if not args.folder:
        args.folder = f'{datetime.now().strftime("%Y-%m-%d_%H:%M:%S")}_{args.bitwidth}b_{args.matsize}m'

    tpusim = TPUSim(args.prog, args.hostmem, args.weightsmem, args.bitwidth,
                    args.matsize, args.folder)
    tpusim.run()
    utils.print_mems(tpusim.host_memory, tpusim.weight_memory, 
                     tpusim.unified_buffer, tpusim.fifo_to_np(), 
                     tpusim.accumulator, args.matsize)
