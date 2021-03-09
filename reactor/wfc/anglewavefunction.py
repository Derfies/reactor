import math

import numpy as np
import numpy.ma as ma
from tabulate import tabulate

from reactor.const import Angle
from reactor.wfc.wavefunctionbase import WavefunctionBase, Contradiction


class AngleWavefunction(WavefunctionBase):

    """
    Use this to replace the current cyclic layouter, however it doesn't so
    edge lengths.

    Do we care? What does that mean?

    Improvements:
    - Use masking instead of slice to get block states?
    - Use node num incident edges to adjust entropy?

    """

    def __init__(self, g, block_g):
        super().__init__()

        self.g = g
        self.block_g = block_g

        total_num_angles = 0
        self.block_sizes = []
        self.node_to_coordses = {}
        #self.block_to_coordses = {}
        self.coords_to_node = {}
        self.coords_to_block = {}
        self.indices_to_block_indices = {}

        i = 0
        self.nodes = []
        for block_index, block in enumerate(self.block_g):
            num_angles = len(block)
            total_num_angles += num_angles
            self.block_sizes.extend([num_angles] * num_angles)
            #self.block_to_coordses[block] = set()
            block_indices = set()
            for node in block.nodes_forward:
                coords = (i,)
                block_indices.add(coords)
                self.indices_to_block_indices[coords] = block_indices
                self.node_to_coordses.setdefault(node, set()).add(coords)
                #self.block_to_coordses[block].add(coords)
                self.coords_to_node[coords] = node
                self.coords_to_block[coords] = block
                self.nodes.append(node + f'\n[{block_index}]')
                i += 1

        # for foo in self.indices_to_block_indices:
        #     print(foo, '->', self.indices_to_block_indices[foo])
        # raise

        self.tiles = list(Angle)
        self.absolute_angles = list(map(Angle.absolute, self.tiles))

        # Wave shape is 2D - dim 1 is the number of angle variants and dim 2 is
        # how many angles we have.
        shape = (total_num_angles,)
        final_shape = (len(self.tiles),) + shape
        self.wave = np.ones(final_shape, dtype=bool)

        # Set up masks.
        # TODO: Create dict that maps indices directly to masks..?
        i = 0
        node_to_masked = {}
        self.index_to_block_array = {}
        self.index_to_node_array = {}
        for block in self.block_g:
            block_masked = ma.masked_array(self.wave, mask=True)
            block_masked.mask[(slice(None), slice(i, i + len(block)))] = False
            for node in block.nodes_forward:
                node_masked = node_to_masked.get(node)
                if node_masked is None:
                    node_to_masked[node] = ma.masked_array(self.wave, mask=True)
                    node_masked = node_to_masked[node]
                node_masked.mask[(slice(None), i)] = False
                self.index_to_block_array[(i,)] = block_masked
                self.index_to_node_array[(i,)] = node_masked
                i += 1

    def constrain(self, array, angle):
        unresolved = np.count_nonzero(array, axis=0) > 1
        angle_index = self.tiles.index(angle)
        constrain_indices = array[angle_index] & unresolved
        array[angle_index][constrain_indices] = False
        return zip(*np.nonzero(constrain_indices))

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
        if (
            self.is_collapsed(array) and
            sum_angles != 360 or
            sum_angles > 360
        ):
            raise Contradiction()

    def check_sum_node_angle(self, array):
        num_neighbors = len(list(self.g.neighbors(node)))
        node_coords = self.node_to_coordses[node]
        node_coord = next(iter(node_coords))
        node_mask = self.node_coords_to_masked[node_coord]
        sum_angles = self.get_sum_resolved_angles(node_mask, absolute=True)
        self.assertTrue(sum_angles <= 360, f'Seed: {seed}')

        num_nonzero = np.count_nonzero(node_mask, axis=0)
        num_indices = num_nonzero.count()
        if num_neighbors == num_indices:
            self.assertEqual(sum_angles, 360, f'Seed: {seed}')

    def resolve_block(self, cur_coords):

        block_mask = self.index_to_block_array[cur_coords]
        block = self.coords_to_block[cur_coords]
        #print('\nBLOCK START:', cur_coords, block)
        #self.debug(block_mask, title='BEFORE')

        propagate = set()
        last_sum = block_mask.sum()
        while True:

            # Find those indices which are unresolved.
            unresolved = np.count_nonzero(block_mask, axis=0) > 1
            unresolved_indices = list(zip(*np.nonzero(unresolved)))

            # Find the sum of the resolved interior angles of the block.
            sum_angles = self.get_sum_resolved_angles(block_mask)

            # Calculate the number of 90 degree turns required to close the
            # shape. If the number of angles required is larger than the number
            # of unresolved indices the shape can never be closed.
            remaining = 360 - sum_angles
            num_required_angles = int(remaining / 90)
            if num_required_angles > len(unresolved_indices):
                raise Contradiction(f'More angles required than uncollapsed indices [{block}]')

            # If the number of required angles is equal to or one less than the
            # the number of unresolved indices we can remove some possibilities.
            if len(unresolved_indices) - num_required_angles < 2:

                # Work out which angle is required to close the shape and which
                # is the opposite angle.
                angle_sign = math.copysign(1, remaining)
                opposite_angle = Angle(-angle_sign * 90)

                constraint_indices = self.constrain(block_mask, opposite_angle)
                #for constraint_index in list(constraint_indices):
                    #print('    Remove:', opposite_angle, 'from node:', self.coords_to_node[constraint_index], 'of block:', self.coords_to_block[constraint_index])
                propagate.update(constraint_indices)

                if num_required_angles == len(unresolved_indices):
                    constraint_indices = self.constrain(block_mask, Angle.STRAIGHT)
                    #for constraint_index in list(constraint_indices):
                        #print('    Remove:', Angle.STRAIGHT, 'from node:', self.coords_to_node[constraint_index], 'of block:', self.coords_to_block[constraint_index])
                    propagate.update(constraint_indices)
                elif num_required_angles == 0:
                    required_angle = Angle(angle_sign * 90)
                    constraint_indices = self.constrain(block_mask, required_angle)
                    #for constraint_index in list(constraint_indices):
                        #print('    Remove:', Angle.STRAIGHT, 'from node:', self.coords_to_node[constraint_index], 'of block:', self.coords_to_block[constraint_index])
                    propagate.update(constraint_indices)

            if block_mask.sum() == last_sum:
                break
            last_sum = block_mask.sum()

        return propagate

    def resolve_node(self, cur_coords):

        node_mask = self.index_to_node_array[cur_coords]
        num_nonzero = np.count_nonzero(node_mask, axis=0)
        unresolved = num_nonzero > 1

        # If the number of neighbours is greater than the number of coordinates
        # then the node lies on the exterior face which needs to be accounted
        # for.
        node = self.coords_to_node[cur_coords]
        num_neighbors = len(list(self.g.neighbors(node)))
        num_indices = num_nonzero.count()   # TODO: Double check.
        num_unresolved = np.count_nonzero(unresolved) + num_neighbors - num_indices

        #print('\nNODE START:', cur_coords, f'[{self.coords_to_node[cur_coords]}]')
        #self.debug(node_mask, title='BEFORE')

        # Find the sum of the resolved angles around the node.
        sum_angles = self.get_sum_resolved_angles(node_mask, absolute=True)

        # Calculate the minimum number of degrees accounted for, this being the
        # sum of the known angles plus at least 90 for each unresolved coord.
        minimum_angles = sum_angles + num_unresolved * Angle.absolute(Angle.INSIDE)
        maximum = 450 - minimum_angles

        # If an angle is less than the maximum remove it as a possibility.
        # TODO: Convert to numpy also? ;)
        propagate = set()
        for angle in (Angle.OUTSIDE, Angle.STRAIGHT):
            if Angle.absolute(angle) <= maximum:
                continue
            constraint_indices = self.constrain(node_mask, angle)
            #for constraint_index in list(constraint_indices):
                #print('    Remove:', angle, 'from node:', self.coords_to_node[constraint_index], 'of block:', self.coords_to_block[constraint_index])
            propagate.update(constraint_indices)

        # Assumptions can be made for the index that lies opposite the current
        # index as it's an explementary angle.
        if num_neighbors == num_indices == 2:
            nonzero_indices = list(zip(*np.nonzero(num_nonzero)))
            nonzero_indices.remove(cur_coords)
            other_coords = nonzero_indices[0]
            this = node_mask[slice(None), cur_coords]
            that = node_mask[slice(None), other_coords]
            this_flipped = np.array([this[1], this[0], this[2]])
            result = this_flipped & that
            xor = np.logical_xor(that, result)
            changed = np.any(xor)
            if changed: # TODO: Make this look like coords from constraint_indices etc
                node_mask[slice(None), other_coords] = result
                propagate.add(other_coords)

                # DEBUG
                # for index, i in enumerate(xor):
                #     if i[0]:
                        #print('    Remove:', self.tiles[index], 'from node:', self.coords_to_node[other_coords], 'of block:', self.coords_to_block[other_coords])

        # TODO: THIS IS NOW BREAKING!
        # If there's a single unresolved index we can infer its value, ie 360 -
        # sum_angles.
        # If the angles remaining equals 90 * num unresolved indices, all
        # remaining must be 90. I think is is handled above...
        # TODO: Put all this into a loop...?
        unresolved = np.count_nonzero(node_mask, axis=0) > 1
        if num_neighbors == num_indices and np.count_nonzero(unresolved) == 1:
            sum_angles = self.get_sum_resolved_angles(node_mask, absolute=True)
            remaining = 360 - sum_angles
            unresolved_index = list(zip(*np.nonzero(unresolved)))[0]
            result = np.array([[False], [False], [False]])
            tile = Angle(180 - remaining)  # Should hopefully break if known_remainder is 360
            result[self.tiles.index(tile)] = [True]
            node_mask[slice(None), unresolved_index] = result

        return propagate

    def get_min_entropy_coords_offset(self):
        return self.block_sizes + super().get_min_entropy_coords_offset()

    def propagate(self, index):
        stack = [index]
        while stack:
            cur_index = stack.pop()
            #self.debug(self.wave, title=f'PROPAGATE: {cur_index}')

            # Attempt to resolve the block array. The node array must be checked
            # for any index returned here.
            dirty_block_indices = set()
            block_array = self.index_to_block_array[cur_index]
            if not self.is_collapsed(block_array):
                dirty_block_indices.update(self.resolve_block(cur_index))

            # Attempt to resolve the node array. Note that this may further
            # collapse the block array.
            dirty_node_indices = set()
            for block_index in dirty_block_indices:
                node_array = self.index_to_node_array[block_index]
                if not self.is_collapsed(node_array):
                    dirty_node_indices.update(self.resolve_node(block_index))
                    self.check_contradiction(node_array)
                    #self.check_sum_node_angle(node_array)

            self.check_contradiction(block_array)
            self.check_sum_block_angle(block_array)

            stack.extend(dirty_block_indices)
            stack.extend(dirty_node_indices)
            #print('STACK:', stack)

    def run(self):

        # There's a number of indices we can collapse straight off the bat, so
        # run each index through the propragation function before we start the
        # default loop.
        for index in range(np.size(self.wave, axis=1)):
            self.propagate((index,))

        #self.debug(self.wave, title='*****INITIAL PROPAGATE OVER*****')

        # Run default loop.
        if not self.is_collapsed(self.wave):
            super().run()

    def on_backtrack(self, coords, original):
        super().on_backtrack(coords, original)

        # Ugly. We need to set the original data in all the masked arrays.
        # There must be an easier way to do this...
        for key, value in self.index_to_block_array.items():
            self.index_to_block_array[key] = ma.masked_array(original, mask=value.mask)
        for key, value in self.index_to_node_array.items():
            self.index_to_node_array[key] = ma.masked_array(original, mask=value.mask)

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
        for coord in indices:
            angle_str = str(self.tiles[coord[0]].value)
            angles[coord[1]] = angle_str.rjust(5)

        contra = np.count_nonzero(mask, axis=0) == 0
        indices = list(zip(*np.nonzero(contra)))
        for coord in indices:
            angles[coord[0]] = '~~nan'

        print(tabulate(mask, headers=self.nodes))
        print(tabulate([angles]).replace('~', ' '))
        print('')
