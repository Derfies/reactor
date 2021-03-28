import itertools as it

import numpy as np
from scipy import sparse
import colorama
from tabulate import tabulate


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
INPUT_MATRIX = ['L', 'L', 'C', 'S', 'S']
INPUT_MATRIX2 = [
    ['L', 'L', 'L', 'L'],
    ['L', 'L', 'L', 'L'],
    ['L', 'L', 'L', 'L'],
    ['L', 'C', 'C', 'L'],
    ['C', 'S', 'S', 'C'],
    ['S', 'S', 'S', 'S'],
    ['S', 'S', 'S', 'S'],
]
INPUT_MATRIX2_1 = [
    ['L', 'S'],
    ['S', 'L'],
]
INPUT_MATRIX3 = [
    [
        ['L', 'S'],
        ['S', 'L'],
    ],
    [
        ['X', 'X'],
        ['X', 'X'],
    ],
    # [
    #     ['L', 'S'],
    #     ['S', 'L'],
    # ]
]
INPUT_MATRIX4 = [
    [
        [
            ['L', 'L', 'L', 'L'],
            ['L', 'L', 'L', 'L'],
            ['L', 'L', 'L', 'L'],
            ['L', 'C', 'C', 'L'],
            ['C', 'S', 'S', 'C'],
            ['S', 'S', 'S', 'S'],
            ['S', 'S', 'S', 'S'],
        ],
        [
            ['L', 'L', 'L', 'L'],
            ['L', 'L', 'L', 'L'],
            ['L', 'L', 'L', 'L'],
            ['L', 'C', 'C', 'L'],
            ['C', 'S', 'S', 'C'],
            ['S', 'S', 'S', 'S'],
            ['S', 'S', 'S', 'S'],
        ],
    ],
    [
        [
            ['L', 'L', 'L', 'L'],
            ['L', 'L', 'L', 'L'],
            ['L', 'L', 'L', 'L'],
            ['L', 'C', 'C', 'L'],
            ['C', 'S', 'S', 'C'],
            ['S', 'S', 'S', 'S'],
            ['S', 'S', 'S', 'S'],
        ],
        [
            ['L', 'L', 'L', 'L'],
            ['L', 'L', 'L', 'L'],
            ['L', 'L', 'L', 'L'],
            ['L', 'C', 'C', 'L'],
            ['C', 'S', 'S', 'C'],
            ['S', 'S', 'S', 'S'],
            ['S', 'S', 'S', 'S'],
        ],
    ]
]


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
    print('output shape:', output.shape)

    # How many additional loops we have to do to display an array of dimension
    # N in 2D slices.
    num_shape_dimensions = len(output.shape)
    num_loops = max(num_shape_dimensions - 2, 0)
    print('num additional 2D loops:', num_loops)

    # Number of slices required to get the 2D output. Will be 1 or 2.
    num_slices = num_shape_dimensions - num_loops
    print('num_slices:', num_slices)
    print('-' * 35)

    # Can I do this with slices as above?
    # Yeah but X is down, which I hate. Whatevs.
    for coord in get_shape_coords(output.shape[:num_loops]):
        index = (*coord, *[slice(None)] * num_slices)
        slice_2d = output[index]
        print('\nslice:', index)
        for x in range(slice_2d.shape[0]):
            output_row = slice_2d[x]
            if not np.iterable(output_row):
                output_row = [output_row]
            print(''.join(output_row))


class Wavefunction:

    def __init__(self, shape, weights, compatibilities):

        print('shape:', shape)
        print('weights:', weights)
        print('compatibilities:', compatibilities)

        tiles, weights = zip(*weights.items())
        self.tiles = tiles
        print('tiles:', self.tiles)
        self.weights = np.array(weights, dtype=np.float64)

        final_shape = (len(self.tiles),) + shape
        self.wave = np.ones(final_shape, dtype=bool)

        print('final_shape:', final_shape)
        print('wave:', self.wave)

        self.adj_matrices = self.to_adjacency_matrix(self.tiles, compatibilities)
        for m 
        self.print_adjacencies(self.adj_matrices)

        raise
        # HAXXOR
        # self.wave[0][:][0][0] = False
        # self.wave[1][:][0][0] = False

        print(self.wave)

    @staticmethod
    def to_adjacency_matrix(tiles, compatibilities):
        print('indices:', list(enumerate(tiles)))
        num_tiles = len(tiles)
        adj_matrices = {}
        for d, rules in compatibilities.items():
            m = np.zeros((num_tiles, num_tiles), dtype=bool)
            for rule in rules:
                tile, other_tile = rule
                index = tiles.index(tile)
                other_index = tiles.index(other_tile)
                m[index, other_index] = 1
            adj_matrices[d] = sparse.csr_matrix(m)

        # for d, rules in adj_matrices.items():
        #     print('d:', d)
        #     print(rules)


        return adj_matrices
        
    @classmethod
    def create_from_input_matrix(cls, matrix, size):
        matrix = np.array(matrix)
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
        return cls(size, weights, compatibilities)

    def print_adjacencies(self, array):
        tabulated = []
        for i, r in enumerate(array):
            tabulated.append([self.tiles[i]] + list(r))
        print(tabulate(tabulated))

    def is_collapsed(self):
        num_states = np.count_nonzero(self.wave, axis=0)
        unresolved = num_states > 1
        return not np.any(unresolved)

    def get_min_entropy_coords(self):
        num_states = np.count_nonzero(self.wave, axis=0)
        unresolved = num_states > 1
        rand = np.random.random(self.wave.shape[1:]) * 0.1  # TODO: make const?
        entropy = np.where(
            unresolved,
            num_states + rand,
            np.inf,
        )
        index = np.argmin(entropy)
        return np.unravel_index(index, entropy.shape)

    def collapse(self, coords):
        states = self.wave[(slice(None), *coords)]
        weighted_states = self.weights * states
        weighted_states /= weighted_states.sum()
        index = np.random.choice(self.weights.size, p=weighted_states)
        states[:] = False
        states[index] = True

    def propagate(self):
        last_count = self.wave.sum()

        # could be const
        pad_shape = ((0, 0),) + ((1, 1),) * (len(self.wave.shape) - 1)

        while True:
            padded = np.pad(
                self.wave,
                pad_shape,
                mode='constant',
                constant_values=True
            )
            supports = {}
            for d in self.adj_matrices:

                firsts = [1 + e for e in d]
                dim = self.wave.shape[1:]
                seconds = [
                    dim[i] + firsts[i]
                    for i in range(len(dim))
                ]

                index = [slice(None)]
                for a, b in zip(firsts, seconds):
                    index.append(slice(a, b))

                shifted = padded[tuple(index)]
                supports[d] = (
                    self.adj_matrices[d] @ shifted.reshape(shifted.shape[0], -1)        # Reshapes the 3D array into 2D..?
                ).reshape(shifted.shape) > 0

            for d in supports:
                print('d:', d)
                print(type(supports[d]), supports[d].shape)
                print(supports[d])
                foo = supports[d].reshape((supports[d].shape[0], -1))
                print(tabulate(foo, headers=self.tiles, tablefmt='fancy_grid'))
                self.wave *= supports[d]
            print('WAVE')
            tabulated_wave = []
            for i, r in enumerate(self.wave.reshape(self.wave.shape[0], -1)):
                 tabulated_wave.append([self.tiles[i]] + list(r))

            print(tabulate(tabulated_wave, headers=self.tiles, tablefmt='fancy_grid'))
            if self.wave.sum() == last_count:
                break
            last_count = self.wave.sum()

        if (self.wave.sum(axis=0) == 0).any():
            print('\n*********contradiction??')

    def run(self):
        print('\n\nrun', self.is_collapsed())
        while not self.is_collapsed():
            coords = self.get_min_entropy_coords()
            print('    coords:', coords)
            self.collapse(coords)
            self.propagate()


if __name__ == '__main__':
    np.random.seed(0)

    # Set up a wave and collapse it.
    shape = (1, 2)
    weights = {'L': 1, 'S': 1}
    compatibilities = {
        (0, 1): {('L', 'S')}
    }
    wf = Wavefunction(shape, weights, compatibilities)#.create_from_input_matrix(INPUT_MATRIX3, (2, 3, 5))
    wf.run()

    # Draw output.
    render_colors(wf.wave, TILE_COLOURS, wf.tiles)
