import numpy as np


class TileGenerator:
    def __init__(self, width: int):
        self.width = width
        self.tiles = []

    def tile_gen(self):
        with open("tiles_to_gen.txt", "r") as f:
            lines = f.readlines()
            for line in lines:
                words = line.split()
                if words[0] == "extract":
                    self._generate_extract(int(words[1]), int(words[2]))
                elif words[0] == "acc":
                    self._generate_acc()
                elif words[0] == "cond_br":
                    self._generate_cond_br(int(words[1]), int(words[2]))
                else:  # words[0] == "add"
                    self._generate_add()
        arr = np.asarray(self.tiles)
        np.save("weights.npy", arr.astype(np.int8))

        for tile in self.tiles:
            print(tile)

    def _generate_cond_br(self, true_dest: int, false_dest: int):
        cond_br = np.zeros((self.width, self.width))
        cond_br[self.width - 1][0] = true_dest
        cond_br[self.width - 1][1] = false_dest
        cond_br[self.width - 1][self.width - 1] = 1
        self.tiles.append(cond_br)

    def _generate_extract(self, col: int, dest_col: int):
        extract_array = np.zeros((self.width, self.width))
        extract_array[col][dest_col] = 1
        self.tiles.append(extract_array)

    def _generate_acc(self):
        self.tiles.append(np.identity(self.width))

    def _generate_add(self):
        add_mat = np.zeros((self.width, self.width))
        add_mat[0][0] = 1
        add_mat[1][0] = 1
        self.tiles.append(add_mat)


if __name__ == "__main__":
    tg = TileGenerator(8)
    tg.tile_gen()
