import abc

import numpy as np

from reactor.utils import weighted_shuffle


INDENT = 4


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
        self.depth = 0
        self.path = []

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

    def collapse_to_tile(self, coords, tile, valid_tiles):
        states = self.wave[(slice(None), *coords)]
        last_count = states.sum()
        states[:] = False
        states[self.tiles.index(tile)] = True
        print(f'\n{self.depth * INDENT * " "}COLLAPSE:', coords, f'[{self.coords_to_node[coords]}]', tile, f'DEPTH: {self.depth} PATH: {self.path} VALID: {valid_tiles}')    #f'[{self.coords_to_block[coords]}]
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
        shuffle = weighted_shuffle(list(tile_weights.keys()), list(tile_weights.values()))
        return shuffle

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
                supports[d] = (self.adj_matrices[d] @ shifted.reshape(shifted.shape[0], -1)).reshape(shifted.shape) > 0

            for d in supports:
                self.wave *= supports[d]
            if self.wave.sum() == last_count:
                break
            last_count = self.wave.sum()

        if (self.wave.sum(axis=0) == 0).any():
            print('\n*********contradiction??')

    def recurse(self):
        coords = self.get_min_entropy_coords()
        valid_tiles = self.get_valid_tiles(coords)
        while valid_tiles:
            original = self.wave.copy()
            tile = valid_tiles.pop()
            self.collapse_to_tile(coords, tile, valid_tiles)
            self.depth += 1
            self.path.append(f'{coords} [{self.coords_to_node[coords]}] {tile.name}')
            try:
                self.propagate(coords)
                if not self.is_collapsed(self.wave):
                    self.recurse()
                break       # break here..?
            except Contradiction as e:

                # Something went wrong - set the wave back so we can try a new
                # permutation.
                self.on_backtrack(coords, original)
                self.debug(self.wave,
                           title=f'{self.depth * INDENT * " "}CONTRADICTION: {coords} {e} DEPTH: {self.depth} PATH: {self.path} VALID: {valid_tiles}') #[{self.coords_to_node[coords]}]
                self.depth -= 1
                self.path.pop()
        else:
            raise Contradiction('Ran out of valid tiles')   # I think..?

    def run(self):
        self.recurse()

    def on_backtrack(self, coords, original):
        self.wave = original
