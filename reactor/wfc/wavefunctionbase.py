import abc

import numpy as np


class Contradiction(Exception):
    """Solving could not proceed without backtracking/restarting."""

    pass


class WavefunctionBase(metaclass=abc.ABCMeta):

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

    def is_collapsed(self, wave):
        num_states = np.count_nonzero(wave, axis=0)
        unresolved = num_states > 1
        return not np.any(unresolved)

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
        # print('\nENTROPY:')
        # for index in range(np.size(self.wave, axis=1)):
        #     print('    entropy:', entropy[index], 'offset:', offset[index], 'unresolved:', unresolved[index], 'node:', self.index_to_node[index], 'index:', index, 'block:', self.index_to_block[index])

        index = np.argmin(entropy)
        coords = np.unravel_index(index, entropy.shape)
        #print('    coords:', coords)
        return coords

    def constrain(self, coords, tile):
        """
        Remove the given tile from the list of potential tiles at index.

        """
        states = self.get_state(coords)
        last_count = states.sum()
        states[self.tiles.index(tile)] = False
        return states.sum() != last_count

    def collapse_to_tile(self, coords, tile):
        states = self.get_state(coords)
        last_count = states.sum()
        states[:] = False
        states[self.tiles.index(tile)] = True
        return states.sum() != last_count

    def collapse(self, coords): # TODO: Rename collapse to random..?
        """"Assumes wave is valid."""
        self.debug()
        states = self.get_state(coords)
        weighted_states = self.weights * states
        weighted_states /= weighted_states.sum()
        index = np.random.choice(self.weights.size, p=weighted_states)
        states[:] = False
        states[index] = True

        print('\nCOLLAPSE node:', self.index_to_node[coords[0]], 'index:', coords[0], 'angle:', self.get_tile(coords), 'block:', self.index_to_block[coords[0]])

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

    def run(self):
        while not self.is_collapsed(self.wave):
            original = self.wave.copy()

            # TODO:

            try:
                coords = self.get_min_entropy_coords()
                self.collapse(coords)
                self.propagate(coords)
            except Contradiction:
                self.wave = original
                print('FOUND CONTRADICTION, RETRYING')
                #sys.exit(1)