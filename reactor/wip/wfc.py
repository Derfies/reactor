import itertools as it

import numpy as np
from scipy import sparse
import colorama
from tabulate import tabulate

from reactor.wfc.wavefunctionbase import Contradiction, WavefunctionBase


TILE_COLOURS = {
    'L': colorama.Fore.GREEN,
    'S': colorama.Fore.BLUE,
    'C': colorama.Fore.YELLOW,
    'A': colorama.Fore.CYAN,
    'B': colorama.Fore.MAGENTA,
    'X': colorama.Fore.WHITE,
    'P': colorama.Fore.WHITE,
    'H': colorama.Fore.BLACK,
}


def valid_dirs(coord, matrix_size):
    dirs = []
    for i in range(len(coord)):
        if coord[i] > 0:
            d = [0] * len(coord)
            d[i] = -1
            dirs.append(tuple(d))
        if coord[i] < matrix_size[i] - 1:
            d = [0] * len(coord)
            d[i] = 1
            dirs.append(tuple(d))
    return dirs


def get_shape_coords(shape):
    sizes = [list(range(el)) for el in shape]
    return it.product(*sizes)


def render_colors(wave, colors, tiles):

    # Convert the collapsed wave to an array of tiles with appropriate colour.
    # This effectively removes the first axis of the wave so the resulting
    # output array's size will be one less dimension.
    chars = []
    for coord in get_shape_coords(wave.shape[1:]):
        states = wf.wave[(slice(None), *coord)]
        index = np.argmax(states)
        val = tiles[index]
        color = colors[val]
        chars.append(color + val + colorama.Style.RESET_ALL)
    output = np.array(chars).reshape(*wave.shape[1:])
    #print('output shape:', output.shape)

    # How many additional loops we have to do to display an array of dimension
    # N in 2D slices.
    num_shape_dimensions = len(output.shape)
    num_loops = max(num_shape_dimensions - 2, 0)
    #print('num additional 2D loops:', num_loops)

    # Number of slices required to get the 2D output. Will be 1 or 2.
    num_slices = num_shape_dimensions - num_loops
    #print('num_slices:', num_slices)
    #print('-' * 35)

    # Can I do this with slices as above?
    # Yeah but X is down, which I hate. Whatevs.
    all_output = ''
    for coord in get_shape_coords(output.shape[:num_loops]):
        index = (*coord, *[slice(None)] * num_slices)
        slice_2d = output[index]
        #print('\nslice:', index)
        for x in range(slice_2d.shape[0]):
            output_row = slice_2d[x]
            if not np.iterable(output_row):
                output_row = [output_row]
            print(''.join(output_row))
            all_output += ''.join(output_row)

    return all_output


class Wavefunction(WavefunctionBase):

    def __init__(self, shape, weights, compatibilities):

        print('shape:', shape)
        print('weights:', weights)
        #print('compatibilities:', compatibilities)

        tiles, weights = zip(*weights.items())
        self.tiles = tiles
        #print('tiles:', self.tiles)
        self.weights = np.array(weights, dtype=np.float64)

        final_shape = (len(self.tiles),) + shape
        self.wave = np.ones(final_shape, dtype=bool)

        #print('final_shape:', final_shape)
        #print('wave:', self.wave)

        self.adj_matrices = self.to_adjacency_matrix(self.tiles, compatibilities)


    @staticmethod
    def to_adjacency_matrix(tiles, compatibilities):
        # print('-' * 35)
        # print('to_adjacency_matrix')
        # print('tiles:', tiles)

        #print('indices:', list(enumerate(tiles)))
        num_tiles = len(tiles)
        adj_matrices = {
            d: np.zeros((num_tiles, num_tiles), dtype=bool)
            for d in ((1, 0), (-1, 0), (0, 1), (0, -1))
        }
        for d, rules in compatibilities.items():
            #print('d:', d)
            m = np.zeros((num_tiles, num_tiles), dtype=bool)
            for rule in rules:
                tile, other_tile = rule
                index = tiles.index(tile)
                other_index = tiles.index(other_tile)
                #print('rule:', tile, '->', other_tile, True)
                #m[index, other_index] = 1
                adj_matrices[d][index, other_index] = 1
            #adj_matrices[d] = sparse.csr_matrix(m)

        print(adj_matrices.keys())

            #print(rules)
            # print('m:')
            # print(sparse.csr_matrix(m))
            # print('-' * 35)

        #print('\n\n')
        # for d, rules in adj_matrices.items():
        #     #print('d:', d)
        #     #print(rules)


        return adj_matrices
        
    @classmethod
    def create_from_input_matrix(cls, matrix, size):
        print('-' * 35)
        print('create_from_input_matrix')

        matrix = np.array(matrix)
        print('matrix:', matrix)
        print('matrix.shape:', matrix.shape)
        weights = {}
        compatibilities = {}
        for coords, tile in np.ndenumerate(matrix):
            weights.setdefault(tile, 0)
            weights[tile] += 1
            for d in valid_dirs(coords, matrix.shape):
                other_coords = []
                for i, el in enumerate(coords):
                    other_coords.append(coords[i] + d[i])
                other_tile = matrix[tuple(other_coords)]
                compatibilities.setdefault(d, set()).add((tile, other_tile))
        for d, rules in compatibilities.items():
            print('d:', d)
            for rule in rules:
                print('    rule:', rule)
        print('-' * 35)
        return cls(size, weights, compatibilities)

    def print_adjacencies(self, adjs):
        #print('adjacencies:')
        tabulated = []
        for d, adj in adjs.items():
            print(f'adjacencies for direction: {d}')
            for i, r in enumerate(adj):#.toarray()):
                tabulated.append([self.tiles[i]] + list(r))
            print(tabulate(tabulated, headers=self.tiles))
            print('-' * 35)


if __name__ == '__main__':
    import random
    np.random.seed(0)
    random.seed(0)

    # Set up a wave and collapse it.
    shape = (1, 2)
    weights = {'L': 1, 'S': 1}
    compatibilities = {
        (1, 0): {('L', 'S')}
    }
    wf = Wavefunction(shape, weights, compatibilities)#.create_from_input_matrix(INPUT_MATRIX3, (2, 3, 5))
    wf.run()

    # Draw output.
    render_colors(wf.wave, TILE_COLOURS, wf.tiles)
