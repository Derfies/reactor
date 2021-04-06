import colorama
import numpy as np

from reactor.wfc.adjacencywavefunction import AdjacencyWaveFunction


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
    lines = []
    for line in str(shaped).split('\n'):
        for bad_char in ('[', ']', '\''):
            line = line.replace(bad_char, '').strip()
        new_line = ''
        for char in line.split():
            color = colors[char]
            new_line += color + char + colorama.Style.RESET_ALL
        lines.append(new_line)
    return '\n'.join(lines)


class Wavefunction(AdjacencyWaveFunction):
        
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
    #wf = Wavefunction(compatibilities, shape, weights)
    wf = Wavefunction.create_from_input_matrix(INPUT_MATRIX, (10, 50))
    wf.run()

    # Draw output.
    print(render_colors(wf.wave, TILE_COLOURS, wf.tiles))
