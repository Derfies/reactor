import numpy as np
from scipy import sparse
import colorama

from reactor.wfc.wavefunctionbase import WavefunctionBase


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

INPUT_MATRIX = [
    ['L', 'L', 'L', 'L'],
    ['L', 'L', 'L', 'L'],
    ['L', 'L', 'L', 'L'],
    ['L', 'C', 'C', 'L'],
    ['C', 'S', 'S', 'C'],
    ['S', 'S', 'S', 'S'],
    ['S', 'S', 'S', 'S'],
]


def get_directions(wave):
    directions = []
    len_wave_shape = len(wave.shape) - 1
    for i in range(len_wave_shape):
        for sign in (-1, 1):
            direction = [0] * len_wave_shape
            direction[i] = sign
            directions.append(tuple(direction))
    return directions


def valid_dirs(coord, matrix_size):

    # Merge with get_directions above?
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


def render_colors(wave, colors, tiles):

    # Hack so that numpy doesn't wrap lines.
    np.set_printoptions(edgeitems=30, linewidth=100000)

    # Convert collapsed states to symbols.
    reshaped = wave.reshape(wave.shape[0], -1)
    chars = []
    for index in range(reshaped.shape[1]):
        states = reshaped[(slice(None), index)]
        tile = tiles[np.argmax(states)]
        chars.append(tile)
    shaped = np.array(chars).reshape(*wave.shape[1:])

    # Convert symbols to coloured ascii characters. Converting the array to a
    # string means numpy to working out each 2d slice of the nd array for us
    # automatically.
    print(str(shaped))
    lines = []
    for line in str(shaped).split('\n'):
        print(line)
        for bad_char in ('[', ']', '\''):
            line = line.replace(bad_char, '').strip()
        new_line = ''
        for char in line.split():
            color = colors[char]
            new_line += color + char + colorama.Style.RESET_ALL
        lines.append(new_line)

    return '\n'.join(lines)


class Wavefunction(WavefunctionBase):

    def __init__(self, shape, weights, compatibilities):

        tiles, weights = zip(*weights.items())
        self.tiles = tiles
        self.weights = np.array(weights, dtype=np.float64)

        final_shape = (len(self.tiles),) + shape
        self.wave = np.ones(final_shape, dtype=bool)

        self.adj_matrices = self.to_adjacency_matrix(self.tiles, compatibilities)

    def to_adjacency_matrix(self, tiles, compatibilities):
        # TODO: Use sparse.csr_matrix(m)
        num_tiles = len(tiles)
        adj_matrices = {
            direction: np.zeros((num_tiles, num_tiles), dtype=bool)
            for direction in get_directions(self.wave)
        }
        for d, rules in compatibilities.items():
            for rule in rules:
                tile, other_tile = rule
                index, other_index = tiles.index(tile), tiles.index(other_tile)
                adj_matrices[d][index, other_index] = 1
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
        return cls(size, weights, compatibilities)


if __name__ == '__main__':
    import random
    np.random.seed(0)
    random.seed(0)

    # Set up a wave and collapse it.
    shape = (5, 5, 5)
    weights = {'L': 1, 'S': 1, 'X': 1}

    # (0, 1) - Appears to be one column to the right
    compatibilities = {
        (1, 0, 0): {
            #('L', 'L'),
            #('X', 'X'),
            ('X', 'L'),
            ('L', 'X'),
        },
        (-1, 0, 0): {
            #('L', 'L'),
            #('X', 'X'),
            ('X', 'L'),
            ('L', 'X'),
        },
        (0, 1, 0): {
            ('L', 'L'),
            ('X', 'X'),
        },
        (0, -1, 0): {
            ('L', 'L'),
            ('X', 'X'),
        },
        (0, 0, 1): {
            ('L', 'L'),
            ('X', 'X'),
        },
        (0, 0, -1): {
            ('L', 'L'),
            ('X', 'X'),
        },
    }
    #wf = Wavefunction(shape, weights, compatibilities)
    wf = Wavefunction.create_from_input_matrix(INPUT_MATRIX, (10, 50))
    wf.run()

    # Draw output.
    print(render_colors(wf.wave, TILE_COLOURS, wf.tiles))