def concat_vec(vec, bits=8):
    t = 0
    mask = int('1'*bits, 2)
    for x in reversed(vec):
        t = (t<<bits) | (int(x) & mask)
    return t

print(f"concat_vec([1, 2, 3, 4]) = {concat_vec([1, 2, 3, 4])}")
print(f"concat_vec([0]) = {concat_vec([0])}")
print(f"concat_vec([0, 0, 0, 0]) = {concat_vec([0, 0, 0, 0])}")
print(f"concat_vec([1, 0, 0, 0]) = {concat_vec([1, 0, 0, 0])}")
print(f"concat_vec([0, 0, 0, 1]) = {concat_vec([0, 0, 0, 1])}")
print()

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

print(f"concat_tile([[1, 2, 3, 4]]) = {concat_tile([[1, 2, 3, 4]])}")
print(f"concat_tile([[1, 2], [3, 4]]) = {concat_tile([[1, 2], [3, 4]])}")
print(f"concat_tile([[], [1], [], [2, 3], [4], []]) = {concat_tile([[], [1], [], [2, 3], [4], []])}")
print()


def make_vec(value, bits=8):
    vec = []
    mask = int('1'*bits, 2)
    while value > 0:
        vec.append(value & mask)
        value = value >> 8
    return list(reversed(vec))

print(f"make_vec(4*2**24 + 3*2**16 + 2*2**8 + 1) = {make_vec(4*2**24 + 3*2**16 + 2*2**8 + 1)}")
print()


def print_mem(mem):
    ks = sorted(mem.keys())
    for a in ks:
        print(a, make_vec(mem[a]))
        

print('print_mem(["key1": 16909060, "key2": 16909061]):')
print_mem({"key1": 16909060, "key2": 16909061})

def print_weight_mem(mem, bits=8, size=8):
    ks = sorted(mem.keys())
    mask = int('1'*(size*bits), 2)
    vecs = []
    for a in ks:
        vec = []
        tile = mem[a]
        while tile > 0:
            vec.append(make_vec(tile & mask))
            tile = tile >> (8*8)
        if vec != []:
            vecs.append(vec)
    for a, vec in enumerate(vecs):
        print(a, list(reversed(vec)))
        
print('print_weight_mem(["key1": 16909060, "key2": 16909061]):')
print_weight_mem({"key1": 0x0102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f202122232425262728292a2b2c2d2e2f303132333435363738393a3b3c3d3e3f4041, "key2": 0x2ffffffffffffffff})