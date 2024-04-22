# for testing how decode() works
import isa

program = open('boston.out', 'rb')
opcode = ""
while (opcode != 'HLT'):
	opcode = int.from_bytes(program.read(isa.OP_SIZE), byteorder='big')
	opcode = isa.BIN2OPCODE[opcode]

	flag = int.from_bytes(program.read(isa.FLAGS_SIZE), byteorder='big')
	length = int.from_bytes(program.read(isa.LEN_SIZE), byteorder='big')
	src_addr = int.from_bytes(program.read(isa.ADDR_SIZE), byteorder='big')
	dest_addr = int.from_bytes(program.read(isa.UB_ADDR_SIZE), byteorder='big')
	print('{} decoding: len {}, flags {}, src {}, dst {}'.format(opcode, length, flag, src_addr, dest_addr))
        