import abc

import numpy as np

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
        weights = [1, 1, 1]

        self.weights = np.array(weights, dtype=np.float64)

    def get_state(self, coords):
        return self.wave[(slice(None), *coords)]

    def get_tile(self, coords):
        states = self.get_state(coords)
        nonzero = np.nonzero(states)
        indices = nonzero[0]
        assert indices.size == 1, 'Cannot resolve the tile'
        return self.tiles[indices[0]]

    # def get_tiles(self, coords):
    #     states = self.get_state(coords)
    #     assert self.is_collapsed(states), 'Cannot resolve tiles'
    #     nonzero = np.nonzero(states)
    #
    #     #print('nonzero')
    #     #print(nonzero)
    #     # print(np.argsort(nonzero))
    #     # print(np.argsort(nonzero, axis=1))
    #     # print(np.argsort(nonzero[1]))
    #     # indices = np.take()
    #
    #     # So this is clearly only for 2D... maybe it doesn't even makes sense
    #     # to do this for higher dimensions. If you were to ask "what are the
    #     # tiles in this 3D area?" what order would you expect them to come back
    #     # in?
    #     indices = nonzero[0][np.argsort(nonzero[1])]
    #     return np.take(self.tiles, indices)
    #
    #     #tiles = np.take(self.tiles, nonzero[0])
    #     # print('nonzero:', nonzero)
    #     # nonzero = np.sort(nonzero, axis=1)
    #     # print('nonzero:', nonzero)
    #     #return nonzero#np.sort(nonzero, axis=1)
    #     #indices = nonzero[0]
    #     #assert indices.size == 1, 'Cannot resolve the tile'
    #     #return self.tiles[indices[0]]

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

    # def constrain(self, coords, tile):
    #     """
    #     Remove the given tile from the list of potential tiles at index.
    #
    #     """
    #     states = self.get_state(coords)
    #     last_count = states.sum()
    #     states[self.tiles.index(tile)] = False
    #     return states.sum() != last_count

    def collapse_to_tile(self, coords, tile):
        states = self.get_state(coords)
        last_count = states.sum()
        states[:] = False
        states[self.tiles.index(tile)] = True

        print('\nCOLLAPSE node:', self.coords_to_node[coords], 'coords:', coords, 'angle:', self.get_tile(coords), 'block:', self.coords_to_block[coords])

        return states.sum() != last_count

    # def collapse(self, coords): # TODO: Rename collapse to random..?
    #     """"Assumes wave is valid."""
    #     self.debug()
    #     states = self.get_state(coords)
    #     weighted_states = self.weights * states
    #     weighted_states /= weighted_states.sum()
    #     index = np.random.choice(self.weights.size, p=weighted_states)
    #     states[:] = False
    #     states[index] = True
    #
    #     print('\nCOLLAPSE node:', self.index_to_node[coords[0]], 'index:', coords[0], 'angle:', self.get_tile(coords), 'block:', self.index_to_block[coords[0]])

    def get_valid_tiles(self, coords):
        states = self.get_state(coords)
        weighted_states = self.weights * states
        weighted_states /= weighted_states.sum()

        tile_weights = {
            tile: weighted_states[i]
            for i, tile in enumerate(self.tiles)
            if weighted_states[i]
        }
        # print('coords:', coords)
        # print('tile weights:', tile_weights)
        shuffle = weighted_shuffle(list(tile_weights.keys()), list(tile_weights.values()))
        # print('shuffle:', shuffle)
        # rtn = [
        #     item for i, item in enumerate(shuffle) if weighted_states[i]
        # ]
        # return rtn
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
        original = self.wave.copy()
        coords = self.get_min_entropy_coords()
        valid_tiles = self.get_valid_tiles(coords)
        while valid_tiles:
            try:
                tile = valid_tiles.pop()
                self.collapse_to_tile(coords, tile)
                self.propagate(coords)
                if not self.is_collapsed(self.wave):
                    self.recurse()
                break       # break here..?
            except Contradiction as e:
                print('FOUND CONTRADICTION, RETRYING:', coords)
                print(e)

                # Something went wrong - set the wave back so we can try a new
                # permutation.
                self.on_backtrack(coords, original)

        else:
            raise Contradiction()   # I think..?

    def run(self):
        self.recurse()

    def on_backtrack(self, coords, original):
        self.wave = original

