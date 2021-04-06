import math

import numpy as np
import numpy.ma as ma
from tabulate import tabulate

from reactor.const import Angle
from reactor.wfc.wavefunctionbase import Contradiction, WaveFunctionBase


class AngleWaveFunction(WaveFunctionBase):

    def __init__(self, g, block_g):

        # Wave shape is 2D - dim 1 is the number of angle variants and dim 2 is
        # how many angles we have.
        total_num_angles = sum([len(b) for b in block_g])
        shape = (total_num_angles,)

        # Tiles are each angle. Stub out ones for each weight.
        tile_weights = {angle: 1 for angle in list(Angle)}
        super().__init__(shape, tile_weights)

        self.block_g = block_g  # TODO: only need this for debug.. remove?
        self.absolute_angles = list(map(Angle.absolute, self.tiles))

        # Set up masks.
        i = 0
        self.nodes = []
        self.indices = []
        self.index_to_node_array = {}
        self.index_to_block_array = {}
        self.index_to_num_neighbors = {}
        self.block_sizes = []
        node_to_masked = {}
        for block_index, block in enumerate(self.block_g):
            num_angles = len(block)
            self.block_sizes.extend([num_angles] * num_angles)
            block_masked = ma.masked_array(self.wave, mask=True)
            block_masked.mask[(slice(None), slice(i, i + num_angles))] = False
            for node in block.nodes_forward:
                node_masked = node_to_masked.get(node)
                if node_masked is None:
                    node_to_masked[node] = ma.masked_array(self.wave, mask=True)
                    node_masked = node_to_masked[node]
                node_masked.mask[(slice(None), i)] = False
                index = (i,)
                self.nodes.append(node + f'\n[{block_index}]')
                self.indices.append(index)
                self.index_to_node_array[index] = node_masked
                self.index_to_block_array[index] = block_masked
                self.index_to_num_neighbors[index] = len(list(g.neighbors(node)))
                i += 1

    def get_min_entropy_coords_offset(self):
        return super().get_min_entropy_coords_offset() + self.block_sizes

    def constrain(self, array, indices):
        """
        Constrain the given array by setting those columns that are unresolved
        to False for the given angle indices. Return only the indices of columns
        that have changed during the operation.

        """
        unresolved = np.count_nonzero(array, axis=0) > 1
        mesh = np.ix_(indices, unresolved)
        changed_mesh_indices = np.count_nonzero(array[mesh], axis=0) > 0
        unresolved_indices = np.nonzero(unresolved)[0]
        array[mesh] = False
        return zip(unresolved_indices[changed_mesh_indices])

    def get_sum_resolved_angles(self, array, absolute=False):
        resolved = np.count_nonzero(array, axis=0) == 1
        resolved_values = array[(slice(None), resolved)]
        resolved_indices = np.nonzero(resolved_values)[0]
        tiles = self.absolute_angles if absolute else self.tiles
        angles = np.take(tiles, resolved_indices)
        return np.sum(angles)

    def check_contradiction(self, array):
        num_nonzero = np.count_nonzero(array, axis=0)
        if not num_nonzero.all():
            raise Contradiction()

    def check_sum_block_angle(self, array):
        sum_angles = self.get_sum_resolved_angles(array)
        if self.is_collapsed(array) and sum_angles != 360:
            raise Contradiction()

    def check_sum_node_angle(self, array):
        mask_non_zero = np.count_nonzero(array.mask == 0, axis=0) > 0
        index = list(zip(*np.nonzero(mask_non_zero)))[0]
        num_indices = np.count_nonzero(array, axis=0).count()
        sum_angles = self.get_sum_resolved_angles(array, absolute=True)
        if (
            self.is_collapsed(array) and
            self.index_to_num_neighbors[index] == num_indices and
            sum_angles != 360 or
            sum_angles > 360
        ):
            raise Contradiction()

    def resolve_block(self, cur_index):
        block_array = self.index_to_block_array[cur_index]
        propagate = set()
        last_sum = block_array.sum()
        while True:

            # Calculate the number of 90 degree turns required to close the
            # face. If the number of angles required is larger than the number
            # of unresolved indices the face can never be closed.
            sum_angles = self.get_sum_resolved_angles(block_array)
            remaining = 360 - sum_angles
            num_required_angles = int(remaining / 90)
            unresolved = np.count_nonzero(block_array, axis=0) > 1
            num_unresolved = np.count_nonzero(unresolved)
            if num_required_angles > num_unresolved:
                raise Contradiction(f'More angles required than uncollapsed indices [{self.index_to_block_array[cur_index]}]')

            # If the number of required angles is equal to or one less than the
            # the number of unresolved indices we can remove some possibilities.
            if num_unresolved - num_required_angles <= 1:

                # Work out which angle is required to close the face and which
                # is the opposite angle.
                angle_sign = math.copysign(1, remaining)
                required_angle = self.tiles.index(Angle(angle_sign * 90))
                opposite_angle = self.tiles.index(Angle(-angle_sign * 90))
                straight_angle = self.tiles.index(Angle.STRAIGHT)

                # If there are no angles required then the angle *must* be
                # straight.
                propagate.update(self.constrain(block_array, [opposite_angle]))
                if num_required_angles == num_unresolved:
                    propagate.update(self.constrain(block_array, [straight_angle]))
                elif num_required_angles == 0:
                    propagate.update(self.constrain(block_array, [required_angle]))

            if block_array.sum() == last_sum:
                break
            last_sum = block_array.sum()

        return propagate

    def resolve_node(self, cur_index):
        num_neighbors = self.index_to_num_neighbors[cur_index]
        node_array = self.index_to_node_array[cur_index]
        propagate = set()
        last_sum = node_array.sum()
        while True:

            # Calculate the minimum number of degrees accounted for around the
            # node, this being the sum of the known angles plus at least 90
            # degrees for each unknown angle. Any angle which is less than this
            # can be removed as a possibility.
            num_nonzero = np.count_nonzero(node_array, axis=0)
            unresolved = num_nonzero > 1
            num_indices = num_nonzero.count()
            num_unresolved = np.count_nonzero(unresolved) + num_neighbors - num_indices
            sum_angles = self.get_sum_resolved_angles(node_array, absolute=True)
            minimum_angles = sum_angles + num_unresolved * Angle.absolute(Angle.INSIDE)
            maximum = 450 - minimum_angles
            constrain_indices = np.nonzero(self.absolute_angles > maximum)[0]
            propagate.update(self.constrain(node_array, constrain_indices))

            # Assumptions can be made for the index that lies opposite the
            # current index as it's an explementary angle.
            if num_neighbors == num_indices == 2:
                nonzero_indices = list(zip(*np.nonzero(num_nonzero)))
                nonzero_indices.remove(cur_index)
                other_index = nonzero_indices[0]
                this = node_array[slice(None), cur_index]
                that = node_array[slice(None), other_index]

                # TODO: Might be able to use matmult here. This sets the other
                # index to the complemet of this one, which may mask some
                # contradictions.
                this_flipped = np.array([this[1], this[0], this[2]])
                result = this_flipped & that
                xor = np.logical_xor(that, result)
                if np.any(xor):
                    node_array[slice(None), other_index] = result
                    propagate.add(other_index)

            # If there's a single unresolved index we can infer its value, ie
            # 360 - sum_angles. No need to propagate.
            if num_neighbors == num_indices and num_unresolved == 1:
                remaining = Angle.absolute(360 - sum_angles)    # TODO: Rename absolute to "switch"?
                constrain_indices = np.nonzero(self.absolute_angles != remaining)[0]
                self.constrain(node_array, constrain_indices)

            if node_array.sum() == last_sum:
                break
            last_sum = node_array.sum()

        return propagate

    def propagate(self, index):
        stack = [index]
        while stack:
            cur_index = stack.pop()

            # Attempt to resolve the block array. The node array must be checked
            # for any index returned here.
            dirty_block_indices = set()
            block_array = self.index_to_block_array[cur_index]
            if not self.is_collapsed(block_array):
                dirty_block_indices.update(self.resolve_block(cur_index))

            # Attempt to resolve the node array. Note that this may further
            # collapse the block array.
            dirty_node_indices = set()
            for block_index in dirty_block_indices.union({cur_index}):
                node_array = self.index_to_node_array[block_index]
                if not self.is_collapsed(node_array):
                    dirty_node_indices.update(self.resolve_node(block_index))

                    # Check for illegal node array data transformations.
                    self.check_contradiction(node_array)
                    self.check_sum_node_angle(node_array)

            # Check for illegal block array data transformations.
            self.check_contradiction(block_array)
            self.check_sum_block_angle(block_array)

            stack.extend(dirty_block_indices)
            stack.extend(dirty_node_indices)

    def backtrack(self, index, original):
        super().backtrack(index, original)

        # Ugly. We need to set the original data in all the masked arrays.
        # There must be an easier way to do this...
        for key, value in self.index_to_block_array.items():
            self.index_to_block_array[key] = ma.masked_array(original, mask=value.mask)
        for key, value in self.index_to_node_array.items():
            self.index_to_node_array[key] = ma.masked_array(original, mask=value.mask)

    def run(self):

        # There's a number of indices we can collapse straight off the bat, so
        # run each index through the propagation function before we start the
        # default loop.
        for index in self.indices:
            self.propagate(index)

        # Run default loop.
        if not self.is_collapsed(self.wave):
            super().run()

    def debug(self, mask, title=None):
        print('')

        if title is not None:
            print(title)
        print(tabulate(enumerate(self.block_g)))

        resolved = np.count_nonzero(mask, axis=0) == 1
        angles = ['~~~~?'] * mask.shape[1]
        if hasattr(mask, 'mask'):
            for i, mask_index in enumerate(mask.mask[0]):
                if mask_index:
                    angles[i] = '~~~~~'
        indices = list(zip(*np.nonzero(mask & resolved)))
        for index in indices:
            angle_str = str(self.tiles[index[0]].value)
            angles[index[1]] = angle_str.rjust(5)

        contra = np.count_nonzero(mask, axis=0) == 0
        indices = list(zip(*np.nonzero(contra)))
        for index in indices:
            angles[index[0]] = '~~nan'

        print(tabulate(mask, headers=self.nodes))
        print(tabulate([angles]).replace('~', ' '))
        print('')
