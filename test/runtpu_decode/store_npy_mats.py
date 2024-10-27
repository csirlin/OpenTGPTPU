import numpy as np


input = np.zeros((3, 32))
weights = np.zeros((8, 8, 8))

np.save('input.npy', input)
np.save('weights.npy', weights)