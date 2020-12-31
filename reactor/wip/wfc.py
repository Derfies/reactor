import numpy as np
from scipy import sparse
import colorama


UP = (0, 1)
LEFT = (-1, 0)
DOWN = (0, -1)
RIGHT = (1, 0)
DIRS = [UP, DOWN, LEFT, RIGHT]
INPUT_MATRIX = [
    ['L', 'L', 'L', 'L'],
    ['L', 'L', 'L', 'L'],
    ['L', 'L', 'L', 'L'],
    ['L', 'C', 'C', 'L'],
    ['C', 'S', 'S', 'C'],
    ['S', 'S', 'S', 'S'],
    ['S', 'S', 'S', 'S'],
]
INPUT_MATRIX2 = [
    ['A', 'A', 'A', 'A'],
    ['A', 'A', 'A', 'A'],
    ['A', 'A', 'A', 'A'],
    ['A', 'C', 'C', 'A'],
    ['C', 'B', 'B', 'C'],
    ['C', 'B', 'B', 'C'],
    ['A', 'C', 'C', 'A'],
]


def valid_dirs(coord, matrix_size):
    x, y = coord
    width, height = matrix_size
    dirs = []

    if x > 0:
        dirs.append(LEFT)
    if x < width - 1:
        dirs.append(RIGHT)
    if y > 0:
        dirs.append(DOWN)
    if y < height - 1:
        dirs.append(UP)

    return dirs


def render_colors(wave, colors, tiles):
    for x in range(wave.shape[1]):
        output_row = []
        for y in range(wave.shape[2]):
            states = wf.wave[(slice(None), *(x, y))]
            index = np.argmax(states)
            val = tiles[index]
            color = colors[val]
            output_row.append(color + val + colorama.Style.RESET_ALL)
        print(''.join(output_row))


class Wavefunction:

    def __init__(self, shape, weights, compatibilities):

        tiles, weights = zip(*weights.items())
        self.tiles = tiles
        self.weights = np.array(weights, dtype=np.float64)

        final_shape = (len(self.tiles),) + shape
        self.wave = np.ones(final_shape, dtype=bool)

        self.adj_matrices = self.to_adjacency_matrix(self.tiles, compatibilities)

    @staticmethod
    def to_adjacency_matrix(tiles, compatibilities):
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
                other_coords = coords[0] + d[0], coords[1] + d[1]
                other_tile = matrix[other_coords]
                compatibilities.setdefault(d, []).append((tile, other_tile))
        return cls(size, weights, compatibilities)

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
        #print('***********states:', (slice(None), *coords))
        weighted_states = self.weights * states
        weighted_states /= weighted_states.sum()
        index = np.random.choice(self.weights.size, p=weighted_states)
        states[:] = False
        states[index] = True

    def propagate(self):
        last_count = self.wave.sum()

        # could be const
        #pad_shape = (len(self.tiles),) + shape
        print(self.wave.shape, len(self.wave.shape))
        pad_shape = ((0, 0),) + ((1, 1),) * (len(self.wave.shape) - 1)
        print('pad_shape:', pad_shape)

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

                shifted = padded[index]
                supports[d] = (self.adj_matrices[d] @ shifted.reshape(shifted.shape[0], -1)).reshape(shifted.shape) > 0

            for d in supports:
                self.wave *= supports[d]
            if self.wave.sum() == last_count:
                break
            last_count = self.wave.sum()

    def run(self):
        while not self.is_collapsed():
            coords = self.get_min_entropy_coords()
            self.collapse(coords)
            self.propagate()


if __name__ == '__main__':

    # Set up a wave and collapse it.
    wf = Wavefunction.create_from_input_matrix(INPUT_MATRIX, (10, ))
    wf.run()

    # Draw output.
    colors = {
        'L': colorama.Fore.GREEN,
        'S': colorama.Fore.BLUE,
        'C': colorama.Fore.YELLOW,
        'A': colorama.Fore.CYAN,
        'B': colorama.Fore.MAGENTA,
    }
    print('wf.tiles:', wf.tiles)
    print('wf.wave:', wf.wave)
    render_colors(wf.wave, colors, wf.tiles)
