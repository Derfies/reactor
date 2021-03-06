import math
import sys

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

        print('\nINIT:')
        super().__init__()

        self.g = g
        self.block_g = block_g

        total_num_angles = 0
        self.block_to_slice = {}
        self.block_sizes = []
        self.node_to_coordses = {}
        self.block_to_coordses = {}
        self.coords_to_node = {}
        self.coords_to_block = {}

        i = 0
        self.nodes = []
        for block_index, block in enumerate(self.block_g):
            start = total_num_angles
            num_angles = len(block)
            total_num_angles += num_angles
            self.block_sizes.extend([num_angles] * num_angles)
            end = total_num_angles
            self.block_to_slice[block] = (slice(start, end),)
            self.block_to_coordses[block] = set()
            for node in block.nodes_forward:
                coords = (i,)
                self.node_to_coordses.setdefault(node, set()).add(coords)
                self.block_to_coordses[block].add(coords)
                self.coords_to_node[coords] = node
                self.coords_to_block[coords] = block
                self.nodes.append(node)
                i += 1

        self.tiles = list(Angle)

        self.absolute_angles = list(map(Angle.absolute, self.tiles))
        print('    tiles:', self.tiles)

        # Wave shape is 2D - dim 1 is the number of angle variants and dim 2 is
        # how many angles we have.
        shape = (total_num_angles,)
        final_shape = (len(self.tiles),) + shape
        self.wave = np.ones(final_shape, dtype=bool)


        # Set up masks.
        i = 0
        node_to_masked = {}
        self.block_coords_to_masked = {}
        self.node_coords_to_masked = {}
        for block in self.block_g:
            block_masked = ma.masked_array(self.wave, mask=True)
            block_masked.mask[(slice(None), slice(i, i + len(block)))] = False
            for node in block.nodes_forward:
                node_masked = node_to_masked.get(node)
                if node_masked is None:
                    node_to_masked[node] = ma.masked_array(self.wave, mask=True)
                    node_masked = node_to_masked[node]
                node_masked.mask[(slice(None), i)] = False
                self.block_coords_to_masked[(i,)] = block_masked
                self.node_coords_to_masked[(i,)] = node_masked
                i += 1

        for block, mask in self.block_coords_to_masked.items():
            print('block:', block)
            print('mask:')
            print(mask)

        for node, mask in self.node_coords_to_masked.items():
            print('node:', node)
            print('mask:')
            print(mask)



        #sys.exit()

    # def debug_coordses(self, coordses):
    #     for coords in coordses:
    #         node = self.coords_to_node[coords]
    #         state = self.get_state(coords)
    #         is_collapsed = self.is_collapsed(state)
    #         angle = None if not is_collapsed else self.get_tile(coords)
    #         print('    coords:', coords, 'node:', node, is_collapsed, '->', state, angle)

    def propagate_by_block(self, cur_coords):

        block_mask = self.block_coords_to_masked[cur_coords]
        num_nonzero = np.count_nonzero(block_mask, axis=0)
        unresolved = num_nonzero > 1
        if not np.any(unresolved):
            return set()


        block = self.coords_to_block[cur_coords]
        print('\nBLOCK START:', cur_coords, block)

        block_slice = self.block_to_slice[block]
        block_state = self.get_state(block_slice)
        #print(block_state)
        coordses = self.block_to_coordses[block]

        print('')
        print('BEFORE')
        # self.debug_coordses(coordses)
        # print('BLOCK STATE')
        # print(block_state)
        print(tabulate(block_mask, headers=self.nodes))
        #print(block_mask)
        print('')

        # Analyse the indices around the face and calculate total and those
        # which are uncollapsed.
        # Note these angles are relative because any number of angles can be
        # used in a face so long as they add to 360.
        last_sum = block_state.sum()
        propagate = set()
        while True:
            total = 0
            uncollapsed_coordses = []


            for coords in coordses:
                state = self.get_state(coords)
                if self.is_collapsed(state):
                    total += self.get_tile(coords)
                else:
                    uncollapsed_coordses.append(coords)

            # ATTEMPT NEW SCHOOL BLOCK INDICES TRICK HERE
            block_mask = self.block_coords_to_masked[cur_coords]
            # print('block_mask:')
            # print(block_mask)

            # NOT DOING STRAIGHT ANGLE IN EVENT OF 1 ANGLE REMAINING
            # Make up 360
            # If there's a single index remaining it must be straight
            # num_spare_angles is how many additional 90 deg corners we can fit into
            # the shape to make it add to 360
            remaining = 360 - total
            num_required_angles = int(remaining / 90)
            sign = math.copysign(1, remaining)
            required_angle = Angle(sign * 90)
            opposite_angle = Angle(-sign * 90)
            if num_required_angles > len(uncollapsed_coordses):
                raise Contradiction('More angles required than uncollapsed indices')

            for coords in uncollapsed_coordses:
                state = self.get_state(coords)
                if self.is_collapsed(state):  # Probably don't need this?
                    continue

                # TODO: Do len(uncollapsed_coordses) - num_required_angles <= 1?
                node = self.coords_to_node[coords]
                if num_required_angles == len(uncollapsed_coordses):
                    if self.constrain(coords, opposite_angle):
                        print('    Remove:', opposite_angle, 'from node:', node, 'of block:', self.coords_to_block[coords])
                        propagate.add(coords)
                    if self.constrain(coords, Angle.STRAIGHT):
                        print('    Remove:', Angle.STRAIGHT, 'from node:', node, 'of block:', self.coords_to_block[coords])
                        propagate.add(coords)
                elif num_required_angles == len(uncollapsed_coordses) - 1:  # num_required_angles is one less than num uncollapsed indices
                    if self.constrain(coords, opposite_angle):
                        print('    Remove:', opposite_angle, 'from node:', node, 'of block:', self.coords_to_block[coords])
                        propagate.add(coords)
                    if num_required_angles == 0:
                        if self.constrain(coords, required_angle):
                            print('    Remove:', required_angle, 'from node:', node, 'of block:', self.coords_to_block[coords])
                            propagate.add(coords)

            if block_state.sum() == last_sum:
                break
            last_sum = block_state.sum()

            print('')
            print('AFTER')
            # self.debug_coordses(coordses)
            print(tabulate(block_mask, headers=self.nodes))
            print('')

        print('BLOCK END')

        # Iterate over each angle of the block and propagate it.
        for coords in coordses:
            propagate.update(self.propagate_by_node(coords))

        # Ensure there's at least one tile for any index.
        if not np.all(np.count_nonzero(block_mask, axis=0)):
            raise Contradiction('block contradiction')

        return propagate

    def propagate_by_node(self, cur_coords):

        node_mask = self.node_coords_to_masked[cur_coords]
        num_nonzero = np.count_nonzero(node_mask, axis=0)
        unresolved = num_nonzero > 1
        if not np.any(unresolved):
            return set()

        # If the number of neighbours is greater than the number of coordinates
        # then the node lies on the exterior face which needs to be accounted
        # for.
        node = self.coords_to_node[cur_coords]
        num_neighbors = len(list(self.g.neighbors(node)))
        num_indices = num_nonzero.count()
        num_unresolved = np.count_nonzero(unresolved) + num_neighbors - num_indices

        print('\nNODE START:', cur_coords, f'[{self.coords_to_node[cur_coords]}]')
        print('')
        print('BEFORE:')
        print(tabulate(node_mask, headers=self.nodes))
        print('')

        # Find the sum of the resolved angles around the node.
        resolved = num_nonzero == 1
        resolved_values = node_mask[(slice(None), resolved)]
        resolved_indices = np.nonzero(resolved_values)[0]
        angles = np.take(self.absolute_angles, resolved_indices)
        sum_angles = np.sum(angles)

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
            angle_index = self.tiles.index(angle)
            to_constrain = node_mask[angle_index] & unresolved
            node_mask[angle_index][to_constrain] = False
            to_constrain_coords = list(zip(*np.nonzero(to_constrain)))
            for coords in to_constrain_coords:
                print('    Remove:', angle, 'from node:', self.coords_to_node[coords], 'of block:', self.coords_to_block[coords])
            propagate.update(to_constrain_coords)

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
            changed = np.any(np.logical_xor(that, result))
            if changed:
                node_mask[slice(None), other_coords] = result
                propagate.add(other_coords)

        print('')
        print('AFTER:')
        print(tabulate(node_mask, headers=self.nodes))
        print('')

        # Ensure there's at least one tile for any index.
        if not np.all(np.count_nonzero(node_mask, axis=0)):
            raise Contradiction('node contradiction')

        return propagate

    def get_min_entropy_coords_offset(self):
        return self.block_sizes + super().get_min_entropy_coords_offset()

    def propagate(self, coords):

        print('\nPROPAGATE:', coords)

        stack = [coords]
        while stack:
            cur_coords = stack.pop()
            print('\nLOOP START:', cur_coords)#, 'node:', self.coords_to_node[cur_coords], 'block:', self.coords_to_block[cur_coords])
            print(tabulate(self.wave, headers=self.nodes))
            stack.extend(self.propagate_by_block(cur_coords))
            print('STACK:', stack)

            # # Assert block sum is 360.
            # # TODO: Put asserts in central location..?
            # for block in self.block_g:
            #     block_slice = self.block_to_slice[block]
            #     block_state = self.get_state(block_slice)
            #     if self.is_collapsed(block_state):
            #         total = np.sum(self.get_tiles(block_slice))
            #         if total != 360:
            #             print('\nblock:' + str(block) + ' does not add to 360')
            #             self.debug()
            #             sys.exit(1)

    def run(self):

        # There's a number of indices we can collapse straight off the bat, so
        # run each index through the propragation function before we start the
        # default loop.
        for index in range(np.size(self.wave, axis=1)):
            self.propagate((index,))

        print('\n\n\n*****INITIAL PROPAGATE OVER*****\n\n\n')
        #self.debug()

        # Run default loop.
        super().run()

    # def debug(self):
    #     print('\nDEBUG:')
    #     results = {}
    #     for index in range(np.size(self.wave, axis=1)):
    #         coords = (index,)
    #         node = self.coords_to_node[coords]
    #         block = self.coords_to_block[coords]
    #         state = self.get_state(coords)
    #         angle = None
    #         if self.is_collapsed(state):
    #             try:
    #                 angle = self.get_tile(coords)
    #             except:
    #                 angle = 'CONTRADICTION'
    #         results[(block, node)] = angle, state, coords
    #
    #     for block, node in sorted(results, key=lambda bn: len(bn[0])):
    #         angle, state, coords = results[block, node]
    #         print('    ', 'coords:', coords, 'node:', node, 'angle:', angle, 'block:', block, '->', state)

    def on_backtrack(self, coords, original):
        super().on_backtrack(coords, original)

        # Ugly. We need to set the original data in all the masked arrays.
        # There must be an easier way to do this...
        for key, value in self.block_coords_to_masked.items():
            self.block_coords_to_masked[key] = ma.masked_array(original, mask=value.mask)
        for key, value in self.node_coords_to_masked.items():
            self.node_coords_to_masked[key] = ma.masked_array(original, mask=value.mask)
