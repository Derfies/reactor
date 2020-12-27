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
        self.compatibilities = compatibilities
        #self.tiles = list(weights.keys())
        #print('tiles:', self.tiles)
        self.weights = weights
        print('weights:', self.weights)
        shape = (len(self.weights),) + size
        self.wave = np.ones(shape, dtype=bool)

        self.adj = self.make_adj(self.compatibilities, self.tiles)
        
    @classmethod
    def create_from_input_matrix(cls, matrix, size):
        compatibilities = set()
        size = len(matrix), len(matrix[0])
        weights = {}
        for x, row in enumerate(matrix):
            for y, tile in enumerate(row):
                weights.setdefault(tile, 0)
                weights[tile] += 1
                for d in valid_dirs((x, y), size):
                    other_tile = matrix[x + d[0]][y + d[1]]
                    compatibilities.add((tile, other_tile, d))
        return cls(size, compatibilities, weights)
        
    def make_adj(self, compatibilities, patterns):

        # MERGE WITH ABOVE
        print('patterns:', patterns)

        by_dirs = {}
        for c in compatibilities:
            cur_tile, other_tile, d = c
            by_dirs.setdefault(d, []).append((cur_tile, other_tile))

        num_patterns = len(patterns)
        adj_matrices = {}
        for dir_, rules in by_dirs.items():
            m = np.zeros((num_patterns, num_patterns), dtype=bool)
            for rule in rules:
                cur_tile, other_tile = rule
                cur_index = patterns.index(cur_tile)
                other_index = patterns.index(other_tile)
                m[cur_index, other_index] = 1

            adj_matrices[dir_] = sparse.csr_matrix(m)

        return adj_matrices

    def min_entropy_coords(self):
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

    def propagate(self, adj):
        last_count = self.wave.sum()
        while True:
            supports = {}
            padded = np.pad(
                self.wave,
                ((0, 0), (1, 1), (1, 1)),
                mode='constant',
                constant_values=True
            )
            for d in adj:
                dx, dy = d
                shifted = padded[:, 1 + dx: 1 + self.wave.shape[1] + dx, 1 + dy: 1 + self.wave.shape[2] + dy]
                supports[d] = (adj[d] @ shifted.reshape(shifted.shape[0], -1)).reshape(shifted.shape) > 0

            for d in adj:
                self.wave *= supports[d]

            if self.wave.sum() == last_count:
                break
            else:
                last_count = self.wave.sum()


wf = Wavefunction.create_from_input_matrix(INPUT_MATRIX, (3, 3))
print('\nwave:')
print(wf.wave)
coords = wf.min_entropy_coords()
print('coords:', coords)
wf.collapse(coords)
print('\nwave:')
print(wf.wave)
wf.propagate(wf.adj)
print('\nwave:')
print(wf.wave)