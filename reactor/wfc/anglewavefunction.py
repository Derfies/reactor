import math
import sys

import numpy as np
import numpy.ma as ma

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
                i += 1

        self.tiles = list(Angle)
        print('    tiles:', self.tiles)

        # Wave shape is 2D - dim 1 is the number of angle variants and dim 2 is
        # how many angles we have.
        shape = (total_num_angles,)
        final_shape = (len(self.tiles),) + shape
        self.wave = np.ones(final_shape, dtype=bool)

        print('total_num_angles:', total_num_angles)
        # Set up masks.
        i = 0
        self.block_to_masked = {}
        for block_index, block in enumerate(self.block_g):
            # mask = [False] * total_num_angles
            # mask[slice(i, i + len(block))] = [True] * len(block)
            # self.block_to_masked[block] = ma.masked_array(self.wave, colmask=mask)
            print('1')
            print(ma.mask_cols(self.wave))
            print('-' * 35)
            print('2')
            print(ma.mask_rows(self.wave))
            print('-' * 35)
            i += len(block)

        for block, mask in self.block_to_masked.items():
            print('block:', block, '->', mask)

        sys.exit()

    def debug_coordses(self, coordses):
        for coords in coordses:
            node = self.coords_to_node[coords]
            state = self.get_state(coords)
            is_collapsed = self.is_collapsed(state)
            angle = None if not is_collapsed else self.get_tile(coords)
            print('    coords:', coords, 'node:', node, is_collapsed, '->', state, angle)

    def propagate_by_block(self, cur_coords):

        block = self.coords_to_block[cur_coords]
        print('\nBLOCK START:', block)

        block_slice = self.block_to_slice[block]
        block_state = self.get_state(block_slice)
        coordses = self.block_to_coordses[block]

        print('')
        print('BEFORE')
        self.debug_coordses(coordses)
        print('BLOCK STATE')
        print(block_state)
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
            self.debug_coordses(coordses)
            print('')

        # Ensure that all states on the block are non-zero.
        if not np.all(np.count_nonzero(block_state, axis=0)):
            raise Contradiction()

        print('BLOCK END')

        # Iterate over each angle of the block and propagate it.
        for coords in coordses:
            propagate.update(self.propagate_by_node(coords))

        return propagate

    def propagate_by_node(self, cur_coords):

        cur_state = self.get_state(cur_coords)
        last_cur_state_sum = cur_state.sum()

        node = self.coords_to_node[cur_coords]

        print('\nNODE START:', node, '[{}]'.format(cur_coords))

        coordses = self.node_to_coordses[node]
        print('')
        print('BEFORE')
        self.debug_coordses(coordses)
        print('')

        # Analyse the indices around the node and calculate total, total known
        # and num uncollapsed.
        # Note these angles are converted to absolute as a finite number of
        # angles add up to the max allowed for a node, ie 4 * 90 = 360.
        total = 0
        num_uncollapsed_coordses = 0
        for coords in coordses:
            state = self.get_state(coords)
            if self.is_collapsed(state):
                total += Angle.absolute(self.get_tile(coords))
            else:
                num_uncollapsed_coordses += 1

        # Add another 90 if there's a missing face. This difference should only
        # ever be 0 or 1.
        neighbors = list(self.g.neighbors(node))
        num_uncollapsed_coordses += len(neighbors) - len(coordses)

        # The minimum angles are the total plus at least 90 degrees for every
        # unknown. The maximum value for any angle is 450 - the minimum total.
        minimum_total = total + num_uncollapsed_coordses * Angle.absolute(Angle.INSIDE)
        maximum = 450 - minimum_total

        # print('    total:', total)
        # print('    num_uncollapsed_indices:', num_uncollapsed_indices)
        # print('    minimum_total:', minimum_total)
        # print('    maximum:', maximum)

        # TODO: Assert minimum_total != 360? That would mean that we know every
        # angle...? Or can assume every angle?

        propagate = set()
        for coords in coordses:
            state = self.get_state(coords)
            if self.is_collapsed(state):
                continue

            # TODO: Replace with for loop.
            # for angle in list(Angle):
            #   if maximum < angle:
            #       angle_index = self.tiles.index(angle)
            #       state[angle_index] = False

            if maximum <= 180:
                if self.constrain(coords, Angle.OUTSIDE):
                    print('    Remove:', Angle.OUTSIDE, 'from node:', node, 'of block:', self.coords_to_block[coords])
                    propagate.add(coords)
            if maximum <= 90:
                if self.constrain(coords, Angle.STRAIGHT):
                    print('    Remove:', Angle.STRAIGHT, 'from node:', node, 'of block:', self.coords_to_block[coords])
                    propagate.add(coords)

            # If there's a single uncollapsed index then we can assume its
            # value.
            # TODO: The event where num_uncollapsed_indices are equal to 90 *
            # remaining degrees
            if num_uncollapsed_coordses == 1:
                known_remainder = 360 - total
                tile = Angle(180 - known_remainder) # Should hopefully break if known_remainder is 360
                if self.collapse_to_tile(coords, tile):
                    propagate.add(coords)
                    print('    Collapsed to:', tile, 'for node:', node, 'of block:', self.coords_to_block[coords])

        if len(neighbors) == len(coords) == 2:
            state = self.get_state(cur_coords)
            other_coordses = list(coordses)[:]
            other_coordses.remove(cur_coords)
            other_coords = other_coordses[0]
            other_state = self.get_state(other_coords)

            # Do explementary collapsing
            if not state[0] and other_state[1]:
                other_state[1] = False
                print('    Remove:', Angle.OUTSIDE, 'from node:', node, 'of block:', self.coords_to_block[other_coords])
                propagate.add(other_coords)
            if not state[1] and other_state[0]:
                other_state[0] = False
                print('    Remove:', Angle.INSIDE, 'from node:', node, 'of block:', self.coords_to_block[other_coords])
                propagate.add(other_coords)
            if not state[2] and other_state[2]:
                other_state[2] = False
                print('    Remove:', Angle.STRAIGHT, 'from node:', node, 'of block:', self.coords_to_block[other_coords])
                propagate.add(other_coords)

        # TODO:
        # Expand this logic to constrain the reverse of nodes with only two
        # edges. Eg if an angle cannot be 90, then it's fair to say that the
        # explementary angle cannot be 270.

        print('')
        print('AFTER')
        broke = False
        for coords in coordses:
            state = self.get_state(coords)
            node = self.coords_to_node[coords]
            angle = None
            if self.is_collapsed(state):
                try:
                    angle = self.get_tile(coords)
                except:
                    angle = 'CONTRADICTION'
                    broke = True
            print('    coords:', coords, 'node:', node, self.is_collapsed(state), '->', state, angle)
        print('')

        if broke:
            self.debug()
            raise

        print('NODE END')

        return propagate

    def get_min_entropy_coords_offset(self):
        return self.block_sizes + super().get_min_entropy_coords_offset()

    def propagate(self, coords):

        print('\nPROPAGATE:', coords)

        stack = [coords]
        while stack:
            cur_coords = stack.pop()
            print('\nLOOP coords:', cur_coords, 'node:', self.coords_to_node[cur_coords], 'block:', self.coords_to_block[cur_coords])
            stack.extend(self.propagate_by_block(cur_coords))
            print('STACK:', stack)

            # Assert block sum is 360.
            # TODO: Put asserts in central location..?
            for block in self.block_g:
                block_slice = self.block_to_slice[block]
                block_state = self.get_state(block_slice)
                if self.is_collapsed(block_state):
                    total = np.sum(self.get_tiles(block_slice))
                    if total != 360:
                        print('\nblock:' + str(block) + ' does not add to 360')
                        self.debug()
                        sys.exit(1)

    def run(self):

        # There's a number of indices we can collapse straight off the bat, so
        # run each index through the propragation function before we start the
        # default loop.
        for index in range(np.size(self.wave, axis=1)):
            self.propagate((index,))

        print('\n\n\n*****INITIAL PROPAGATE OVER*****\n\n\n')
        self.debug()

        # Run default loop.
        super().run()

    def debug(self):
        print('\nDEBUG:')
        results = {}
        for index in range(np.size(self.wave, axis=1)):
            coords = (index,)
            node = self.coords_to_node[coords]
            block = self.coords_to_block[coords]
            state = self.get_state(coords)
            angle = None
            if self.is_collapsed(state):
                try:
                    angle = self.get_tile(coords)
                except:
                    angle = 'CONTRADICTION'
            results[(block, node)] = angle, state, coords

        for block, node in sorted(results, key=lambda bn: len(bn[0])):
            angle, state, coords = results[block, node]
            print('    ', 'coords:', coords, 'node:', node, 'angle:', angle, 'block:', block, '->', state)