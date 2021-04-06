import colorama
import numpy as np

from reactor.wfc.adjacencywavefunction import AdjacencyWaveFunction
from reactor.wfc.utils import get_colour_output


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


class WaveFunction(AdjacencyWaveFunction):
        
    @classmethod
    def create_from_input_matrix(cls, matrix, shape):
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
        return cls(compatibilities, shape, weights)


if __name__ == '__main__':
    import random
    np.random.seed(0)
    random.seed(0)

    # Set up a wave and collapse it.
    shape = (5, 6, 7)
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
    #wf = WaveFunction(compatibilities, shape, weights)
    wf = WaveFunction.create_from_input_matrix(INPUT_MATRIX, (10, 50))
    wf.run()

    # Draw output.
    print(get_colour_output(wf.wave, TILE_COLOURS, wf.tiles))
