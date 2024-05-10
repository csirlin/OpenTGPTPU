import numpy as np
import pyrtl

# Host mem: N x 13 input matrix
# Weight mem:
# L1: 13x8
# L2: 8x8
# L3: 8x1
np.set_printoptions(linewidth=100)
hm = np.load('boston_input.npy').astype(np.int32) # 10x13 (starts as actually 10x16)
w = np.load('boston_weights.npy').astype(np.int32) # w[0]: 13x8; w[1]: 8x8; w[2]: 8x1 (each starts as 16x16)

# print(f"input ({hm.shape})= {hm}")
# print(f"weights ({w.shape})= {w}")

inw0 = hm[:, :13] @ w[0][:13, :8] #in * w0: 10x8
print(f"in = {hm}")
print(f"w0 = {w[0]}")
print(f"in * w0: 10x8 = {inw0}")
# print(f"in * w0 with np.matmul = {np.matmul(hm, w[0])}")
# print(f"in * w0 no limiting = {hm @ w[0]}")

rinw0 = np.maximum(inw0, 0) # ReLU(in * w0): 10x8
print(f"ReLU(in * w0): 10x8 = {rinw0}")

rinw0w1 = rinw0.astype(np.int8) @ w[1][:8, :8] # ReLU(in @ w0) @ w1: 10x8
print(f"ReLU(in @ w0) @ w1: 10x8 = {rinw0w1}")

rrinw0w1 = np.maximum(rinw0w1, 0) # ReLU(ReLU(in @ w0) @ w1): 10x8
print(f"ReLU(ReLU(in @ w0) @ w1): 10x8 = {rrinw0w1}")

rrinw0w1w2 = rrinw0w1.astype(np.int8) @ w[2][:8, :1] # ReLU(ReLU(in @ w0) @ w1) @ w2: 10x1
print(f"ReLU(ReLU(in @ w0) @ w1) @ w2: 10x1 = {rrinw0w1w2}")

rrrinw0w1w2 = np.maximum(rrinw0w1w2, 0)  # ReLU(ReLU(ReLU(in @ w0) @ w1) @ w2): 10x1
print(f"ReLU(ReLU(ReLU(in @ w0) @ w1) @ w2): 10x1 = {rrrinw0w1w2}")

print(f"Convert to uint8 for final print: 10x1 = {rrrinw0w1w2.astype(np.uint8)}")
