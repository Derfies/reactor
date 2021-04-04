import abc

import numpy as np
from tabulate import tabulate

from reactor.utils import weighted_shuffle


class Contradiction(Exception):
    """Solving could not proceed without backtracking/restarting."""

    pass


class WavefunctionBase(metaclass=abc.ABCMeta):

    @staticmethod
    def is_collapsed(array):
        unresolved = np.count_nonzero(array, axis=0) > 1
        return not np.any(unresolved)

    def __init__(self):
        self.weights = np.array([1, 1, 1], dtype=np.float64)
        self.i = 0

    def get_min_entropy_coords_offset(self):
        return np.random.random(self.wave.shape[1:]) * 0.1  # TODO: make const?

    def get_min_entropy_coords(self):
        num_states = np.count_nonzero(self.wave, axis=0)
        unresolved = num_states > 1
        offset = self.get_min_entropy_coords_offset()
        entropy = np.where(
            unresolved,
            num_states + offset,
            np.inf,
        )
        index = np.argmin(entropy)
        return np.unravel_index(index, entropy.shape)

    def collapse_to_tile(self, coords, tile):
        states = self.wave[(slice(None), *coords)]
        last_count = states.sum()
        states[:] = False
        states[self.tiles.index(tile)] = True
        return states.sum() != last_count

    def get_valid_tiles(self, coords):
        states = self.wave[(slice(None), *coords)]
        weighted_states = self.weights * states
        weighted_states /= weighted_states.sum()
        tile_weights = {
            tile: weighted_states[i]
            for i, tile in enumerate(self.tiles)
            if weighted_states[i]
        }
        return weighted_shuffle(
            list(tile_weights.keys()),
            list(tile_weights.values()),
        )

    def print_array(self, d, s):
        print(d)
        tabulated = []
        foo = s.reshape(s.shape[0], -1)
        for i, r in enumerate(foo):
            tabulated.append([self.tiles[i]] + list(r))
        print(tabulate(tabulated, headers=list(range(len(foo)))))
        print('-' * 35)

    def print_adjacency(self, d, adj):
        #for d, adj in adjs.items():
        print(f'adjacencies: {d}')
        tabulated = []
        for i, r in enumerate(adj):#.toarray()):
            tabulated.append([self.tiles[i]] + list(r))
        print(tabulate(tabulated, headers=self.tiles))
        print('-' * 35)

    def propagate(self, index):
        #print('propagate')
        last_count = self.wave.sum()

        # could be const
        len_wave_shape = len(self.wave.shape) - 1
        pad_shape = ((0, 0),) + ((1, 1),) * len_wave_shape
        i = 0
        #self.print_array('wave:', self.wave)

        while True:
            #print('i:', i)
            supports = {}
            for d in self.adj_matrices:

                shaped = self.wave.reshape(self.wave.shape[0], -1)
                adj = self.adj_matrices[d] @ shaped
                unshaped = adj.reshape(self.wave.shape)

                padded = np.pad(
                    unshaped,
                    pad_shape,
                    mode='constant',
                    constant_values=True
                )

                firsts = [1 + e for e in d]
                dim = self.wave.shape[1:]
                seconds = [
                    dim[i] + firsts[i]
                    for i in range(len(dim))
                ]

                index = [slice(None)]
                for a, b in zip(firsts, seconds):
                    index.append(slice(a, b))
                supports[d] = padded[tuple(index)]

                #self.print_adjacency(d, self.adj_matrices[d])
                #self.print_array('result:', self.wave * (supports[d] > 0))

            for d, s in supports.items():
                self.wave *= (s > 0)

            if self.wave.sum() == last_count:
                break
            last_count = self.wave.sum()

            i += 1

        if (self.wave.sum(axis=0) == 0).any():
            ##print('\n*********contradiction??')
            raise Contradiction()

    def recurse(self):

        coords = self.get_min_entropy_coords()
        valid_tiles = self.get_valid_tiles(coords)
        while valid_tiles:
            original = self.wave.copy()
            tile = valid_tiles.pop()

            self.collapse_to_tile(coords, tile)
            #print('collapse:', coords, '->', tile)

            try:
                self.propagate(coords)
                if not self.is_collapsed(self.wave):
                    self.recurse()
                break       # break here..?
            except Contradiction as e:

                # Something went wrong - set the wave back so we can try a new
                # permutation.
                self.backtrack(coords, original)
                #print('backtrack\n')

        else:
            #raise Contradiction('Ran out of valid tiles')   # I think..?
            #print('EXIT')
            import sys
            sys.exit(1)

    def run(self):
        #print('\n\nRUN\n\n')
        self.recurse()

    def backtrack(self, coords, original):
        self.wave = original
