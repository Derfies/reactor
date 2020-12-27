import numpy as np
from scipy import sparse


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


def valid_dirs(cur_co_ord, matrix_size):
    x, y = cur_co_ord
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


class Wavefunction:

    def __init__(self, size, compatibilities, weights):

        self.adj = compatibilities
        print('compatibilities')
        print(self.adj)

        self.weights = weights
        print('weights:', self.weights)

        shape = (len(self.weights),) + size
        print('shape:', shape)
        self.wave = np.ones(shape, dtype=bool)

    def is_collapsed(self):
        num_states = np.count_nonzero(self.wave, axis=0)
        unresolved = num_states > 1
        return not np.any(unresolved)
        
    @classmethod
    def create_from_input_matrix(cls, matrix, output_size):
        compatibilities = set()
        size = len(matrix), len(matrix[0])
        weights = {}

        by_dirs = {}
        for x, row in enumerate(matrix):
            for y, tile in enumerate(row):
                weights.setdefault(tile, 0)
                weights[tile] += 1
                for d in valid_dirs((x, y), size):
                    other_tile = matrix[x + d[0]][y + d[1]]
                    compatibilities.add((tile, other_tile, d))
                    by_dirs.setdefault(d, []).append((tile, other_tile))

        tiles = list(weights.keys())
        num_tiles = len(tiles)
        adj_matrices = {}
        for dir_, rules in by_dirs.items():
            m = np.zeros((num_tiles, num_tiles), dtype=bool)
            for rule in rules:
                tile, other_tile = rule
                index = tiles.index(tile)
                other_index = tiles.index(other_tile)
                m[index, other_index] = 1

            adj_matrices[dir_] = sparse.csr_matrix(m)


        return cls(output_size, adj_matrices, weights)

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

        # TODO - Encode weights once during __init__.
        weights = np.zeros(len(self.weights), dtype=np.float64)
        for w_id, w_key in enumerate(self.weights):
            w_val = self.weights[w_key]
            weights[w_id] = w_val

        weighted_states = weights * states
        weighted_states /= weighted_states.sum()
        index = np.random.choice(len(self.weights), p=weighted_states)
        states[:] = False
        states[index] = True

    def propagate(self):
        last_count = self.wave.sum()
        while True:
            supports = {}
            padded = np.pad(
                self.wave,
                ((0, 0), (1, 1), (1, 1)),
                mode='constant',
                constant_values=True
            )
            for d in self.adj:
                dx, dy = d
                shifted = padded[:, 1 + dx: 1 + self.wave.shape[1] + dx, 1 + dy: 1 + self.wave.shape[2] + dy]
                supports[d] = (self.adj[d] @ shifted.reshape(shifted.shape[0], -1)).reshape(shifted.shape) > 0

            for d in self.adj:
                self.wave *= supports[d]

            if self.wave.sum() == last_count:
                break
            else:
                last_count = self.wave.sum()


wf = Wavefunction.create_from_input_matrix(INPUT_MATRIX, (30, 30))
print('\nwave:')
print(wf.wave)

#print('is_collapsed:', wf.is_collapsed())

while not wf.is_collapsed():
    coords = wf.get_min_entropy_coords()
    #print('\ncoords:', coords)

    wf.collapse(coords)
    #print('\nwave:')
    #print(wf.wave)
    wf.propagate()
    #print('\nwave:')
    # print('-' * 35)
    # print(wf.wave)



for x in range(wf.wave.shape[1]):
    output_row = []
    for y in range(wf.wave.shape[2]):
        states = wf.wave[(slice(None), *(x, y))]
        #print('states:', np.argmax(states))
        output_row.append(str(np.argmax(states)))
    print(''.join(output_row))