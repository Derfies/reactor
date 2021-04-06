import abc

import numpy as np

from reactor.utils import weighted_shuffle


class Contradiction(Exception):

    """Solving could not proceed without backtracking/restarting."""

    pass


class WavefunctionBase(metaclass=abc.ABCMeta):

    def __init__(self, shape, tile_weights):
        tiles, weights = zip(*tile_weights.items())
        self.tiles = tiles
        self.weights = np.array(weights, dtype=np.float64)
        wave_shape = (len(self.tiles),) + shape
        self.wave = np.ones(wave_shape, dtype=bool)

    @staticmethod
    def is_collapsed(array):
        unresolved = np.count_nonzero(array, axis=0) > 1
        return not np.any(unresolved)

    @property
    def directions(self):
        directions = []
        len_wave_shape = len(self.wave.shape) - 1
        for i in range(len_wave_shape):
            for sign in (-1, 1):
                direction = [0] * len_wave_shape
                direction[i] = sign
                directions.append(tuple(direction))
        return tuple(directions)

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

    @abc.abstractmethod
    def propagate(self, index):
        """"""

    def backtrack(self, coords, original):
        self.wave = original

    def recurse(self):

        # TODO: Might be able to further abstract this into some
        #  "bruteforcesovler" class.
        coords = self.get_min_entropy_coords()
        valid_tiles = self.get_valid_tiles(coords)
        while valid_tiles:
            original = self.wave.copy()
            self.collapse_to_tile(coords, valid_tiles.pop())
            try:
                self.propagate(coords)
                if not self.is_collapsed(self.wave):
                    self.recurse()
                break
            except Contradiction as e:

                # Something went wrong - set the wave back so we can try a new
                # permutation.
                self.backtrack(coords, original)
        else:
            raise Contradiction('Ran out of valid tiles')

    def run(self):
        self.recurse()
