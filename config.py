'''
Hardware configuration.
'''

# MATSIZE = 8
# DWIDTH = 32
# NUM_TILES = 8
# NUM_WEIGHTS = 8

# ADDR_SIZEs need to be sufficient for the addressed used, otherwise it will 
# cause issues in pyrtl.
# squishtests: needs to hold at least 10*MATSIZE rows
# mullifier unit tests: needs to hold EXACTLY 16*MATSIZE rows
# mullifier examples: UB and ACC sizes must be exactly 12
HOST_ADDR_SIZE = 64
UB_ADDR_SIZE = 12
WEIGHT_DRAM_ADDR_SIZE = 40
ACC_ADDR_SIZE = 12 # 16
INSTRUCTION_WIDTH = 14 * 8
IMEM_ADDR_SIZE = 12

# values = [host_addr_size, ub_addr_size, weight_dram_addr_size, acc_addr_size, mat_mul_size, data_width]
#
# def set_config(values):
#     keys = ['HOST_ADDR_SIZE', 'UB_ADDR_SIZE', 'WEIGHT_DRAM_ADDR_SIZE', 'ACC_ADDR_SIZE', 'MAT_MUL_SIZE', 'DATA_WIDTH']
#     return dict(zip(keys, values))
#
# config = {
#         'HOST_ADDR_SIZE': host_addr_size,
#         'UB_ADDR_SIZE': ub_addr_size,
#         'WEIGHT_DRAM_ADDR_SIZE': weight_dram_addr_size,
#         'ACC_ADDR_SIZE': acc_addr_size,
#         'MAT_MUL_SIZE': mat_mul_size,
#         'DATA_WIDTH': data_width,
#         }
