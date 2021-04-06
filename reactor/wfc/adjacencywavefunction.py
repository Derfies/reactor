import numpy as np

from reactor.wfc.wavefunctionbase import Contradiction, WavefunctionBase


class AdjacencyWaveFunction(WavefunctionBase):

    def __init__(self, compatibilities, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Build adjacency matrices.
        self.adj_matrices = self._calculate_adjacency_matrix(compatibilities)

        # Cache array manipulation args.
        self.pad_args = {}
        self.slice_args = {}
        for d in self.directions:
            pad_args, slice_args = [], []
            for i in range(len(self.wave.shape)):
                pad_args.append([0, 0])
                slice_args.append(slice(0, self.wave.shape[i]))

            index = np.nonzero(d)[0][0]
            index2 = 0 if d[index] == -1 else 1
            pad_args[index + 1][index2] = 1
            slice_args[index + 1] = slice(index2, self.wave.shape[index + 1] + index2)
            self.pad_args[d] = pad_args
            self.slice_args[d] = tuple(slice_args)

    def _calculate_adjacency_matrix(self, compatibilities):
        # TODO: Use sparse.csr_matrix(m)
        num_tiles = len(self.tiles)
        adj_matrices = {
            direction: np.zeros((num_tiles, num_tiles), dtype=bool)
            for direction in self.directions
        }
        for d, rules in compatibilities.items():
            for rule in rules:
                tile, other_tile = rule
                index = self.tiles.index(tile)
                other_index = self.tiles.index(other_tile)
                adj_matrices[d][index, other_index] = 1
        return adj_matrices

    def propagate(self, index):
        last_count = self.wave.sum()
        while True:

            # Calculate legal adjacencies.
            supports = {}
            for d in self.adj_matrices:
                shaped = self.wave.reshape(self.wave.shape[0], -1)
                adj = self.adj_matrices[d] @ shaped
                unshaped = adj.reshape(self.wave.shape)
                padded = np.pad(
                    unshaped,
                    self.pad_args[d],
                    mode='constant',
                    constant_values=True
                )
                supports[d] = padded[self.slice_args[d]] > 0
            for s in supports.values():
                self.wave *= s

            # Break if there was no change in state.
            if self.wave.sum() == last_count:
                break
            last_count = self.wave.sum()

        # Can maybe replace with check_contradiction in anglewavefunction.
        if (self.wave.sum(axis=0) == 0).any():
            raise Contradiction()
