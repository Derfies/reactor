import math
import sys

import numpy as np

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

        self.index_to_block = []
        self.block_sizes = []
        #self.index_to_block_index_range = []
        self.block_to_index_range = {}

        num_angles = 0

        self.index_to_node = []

        self.node_to_indices = {}
        m = 0
        wave_index = 0
        for block_index, block in enumerate(self.block_g):
            num_angles += len(block)
            self.index_to_block.extend([block] * len(block))
            self.block_sizes.extend([len(block)] * len(block))
            for i, node in enumerate(block.nodes_forward):
                self.index_to_node.append(node)
                #self.index_to_block_index_range.append((m, m + len(block)))
                self.node_to_indices.setdefault(node, set()).add(wave_index)
                self.block_to_index_range[block] = m, m + len(block)

                wave_index += 1
            m += len(block)

        self.tiles = list(Angle)
        print('    tiles:', self.tiles)

        # Wave shape is 2D - dim 1 is the number of angle variants and dim 2 is
        # how many angles we have.
        print('    num_angles:', num_angles)
        shape = (num_angles,)
        final_shape = (len(self.tiles),) + shape
        self.wave = np.ones(final_shape, dtype=bool)

        print('    block sizes:', self.block_sizes)

    def debug_block(self, block_state, start):
        for index in range(np.size(block_state, axis=1)):
            state = block_state[(slice(None), index)]
            node = self.index_to_node[start + index]
            angle = None
            if self.is_collapsed(state):
                angle = self.get_tile((index + start,))
            print('    index:', index + start, 'node:', node, self.is_collapsed(state), '->', state, angle)

    def debug_node(self, node, indices):
        for index in indices:
            state = self.get_state((index,))
            #node = self.index_to_node[index]
            angle = None
            if self.is_collapsed(state):
                angle = self.get_tile((index,))
            print('    index:', index, 'node:', node, self.is_collapsed(state), '->', state, angle)

    def propagate_by_block(self, block):

        # The angles of the block the index belongs to may be guessed...
        start, stop = self.block_to_index_range[block]
        block_slice = slice(start, stop)
        block_state = self.get_state((block_slice,))
        # if self.is_collapsed(block_state):
        #     return ()

        print('\nBLOCK START:', block)

        print('')
        print('BEFORE')
        self.debug_block(block_state, start)
        print('')

        # Analyse the indices around the face and calculate total and those
        # which are uncollapsed.
        # Note these angles are relative because any number of angles can be
        # used in a face so long as they add to 360.
        propagate = set()
        changed = True
        while changed:
            total = 0
            uncollapsed_indices = []
            for index in range(np.size(block_state, axis=1)):
                state = block_state[(slice(None), index)]
                if self.is_collapsed(state):
                    total += self.get_tile((start + index,))
                else:
                    uncollapsed_indices.append(index)

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
            if num_required_angles > len(uncollapsed_indices):
                #print('More required angles than uncollapsed indices')
                #sys.exit(1)
                raise Contradiction('More required angles than uncollapsed indices')

            this_propagate = set()
            for index in uncollapsed_indices:
                state = block_state[(slice(None), index)]
                if self.is_collapsed(state):  # Probably don't need this?
                    continue

                # Drop the *opposite* angle in events:
                #   num_required_angles == len(uncollapsed_indices)
                #   num_required_angles == len(uncollapsed_indices) + 1
                # Drop the *straight* angle in events:
                #   num_required_angles = 0 and len(uncollapsed_indices) == 1

                node = self.index_to_node[index]

                index = index + start
                if num_required_angles == len(uncollapsed_indices):
                    if self.constrain((index,), opposite_angle):
                        print('    Remove:', opposite_angle, 'from node:', node, 'of block:', self.index_to_block[index])
                        this_propagate.add(index)
                    if self.constrain((index,), Angle.STRAIGHT):
                        print('    Remove:', Angle.STRAIGHT, 'from node:', node, 'of block:', self.index_to_block[index])
                        this_propagate.add(index)
                elif num_required_angles == len(uncollapsed_indices) - 1:
                    if self.constrain((index,), opposite_angle):
                        print('    Remove:', opposite_angle, 'from node:', node, 'of block:', self.index_to_block[index])
                        this_propagate.add(index)
                    if num_required_angles == 0:
                        if self.constrain((index,), required_angle):
                            print('    Remove:', required_angle, 'from node:', node, 'of block:', self.index_to_block[index])
                            this_propagate.add(index)


            if this_propagate:
                propagate.update(this_propagate)
                changed = True
            else:
                changed = False

            for index in range(np.size(block_state, axis=1)):
                state = block_state[(slice(None), index)]
                nonzero = np.nonzero(state)
                if not nonzero[0].size:
                    raise Contradiction()
                #print('nonzero:', nonzero)
                #indices = nonzero[0]
                #assert indices.size == 1, 'Cannot resolve the tile'


            print('')
            print('AFTER')
            self.debug_block(block_state, start)
            print('')

        print('BLOCK END')

        return this_propagate

    def propagate_by_node(self, original_index, node):

        print('\nNODE START:', node, '[{}]'.format(original_index))

        indices = set(self.node_to_indices[node])

        print('')
        print('BEFORE')
        self.debug_node(node, indices)
        print('')

        # Analyse the indices around the node and calculate total, total known
        # and num uncollapsed.
        # Note these angles are converted to absolute as a finite number of
        # angles add up to the max allowed for a node, ie 4 * 90 = 360.
        total = 0
        num_uncollapsed_indices = 0
        for index in indices:
            state = self.get_state((index,))
            if self.is_collapsed(state):
                total += Angle.absolute(self.get_tile((index,)))
            else:
                num_uncollapsed_indices += 1

        # Add another 90 if there's a missing face. This difference should only
        # ever be 0 or 1.
        neighbors = list(self.g.neighbors(node))
        num_uncollapsed_indices += len(neighbors) - len(indices)

        # The minimum angles are the total plus at least 90 degrees for every
        # unknown. The maximum value for any angle is 450 - the minimum total.
        minimum_total = total + num_uncollapsed_indices * Angle.absolute(Angle.INSIDE)
        maximum = 450 - minimum_total

        # print('    total:', total)
        # print('    num_uncollapsed_indices:', num_uncollapsed_indices)
        # print('    minimum_total:', minimum_total)
        # print('    maximum:', maximum)

        # TODO: Assert minimum_total != 360? That would mean that we know every
        # angle...? Or can assume every angle?

        propagate = set()
        for index in indices:
            state = self.get_state((index,))
            if self.is_collapsed(state):    # Probably don't need this? - yes i do, to stop collapsing already collapsed shit.
                continue

            # TODO: Replace with for loop.
            # for angle in list(Angle):
            #   if maximum < angle:
            #       angle_index = self.tiles.index(angle)
            #       state[angle_index] = False

            if maximum <= 180:
                if self.constrain((index,), Angle.OUTSIDE):
                    print('    Remove:', Angle.OUTSIDE, 'from node:', node, 'of block:', self.index_to_block[index])
                    propagate.add(index)
            if maximum <= 90:
                if self.constrain((index,), Angle.STRAIGHT):
                    print('    Remove:', Angle.STRAIGHT, 'from node:', node, 'of block:', self.index_to_block[index])
                    propagate.add(index)

            # If there's a single uncollapsed index then we can assume its
            # value.
            # TODO: The event where num_uncollapsed_indices are equal to 90 *
            # remaining degrees
            if num_uncollapsed_indices == 1:
                known_remainder = 360 - total
                tile = Angle(180 - known_remainder) # Should hopefully break if known_remainder is 360
                if self.collapse_to_tile((index,), tile):
                    propagate.add(index)
                    print('    Collapsed to:', tile, 'for node:', node, 'of block:', self.index_to_block[index])

        if len(neighbors) == len(indices) == 2:

            state = self.get_state((original_index,))

            print('    NEW')

            other_indices = list(indices)[:]
            other_indices.remove(original_index)
            other_index = other_indices[0]
            other_state = self.get_state((other_index,))

            # Do explementary collapsing
            if not state[0] and other_state[1]:
                other_state[1] = False
                print('    Remove:', Angle.OUTSIDE, 'from node:', node, 'of block:', self.index_to_block[other_index])
                propagate.add(other_index)
            if not state[1] and other_state[0]:
                other_state[0] = False
                print('    Remove:', Angle.INSIDE, 'from node:', node, 'of block:', self.index_to_block[other_index])
                propagate.add(other_index)
            if not state[2] and other_state[2]:
                other_state[2] = False
                print('    Remove:', Angle.STRAIGHT, 'from node:', node, 'of block:', self.index_to_block[other_index])
                propagate.add(other_index)

        # TODO:
        # Expand this logic to constrain the reverse of nodes with only two
        # edges. Eg if an angle cannot be 90, then it's fair to say that the
        # explementary angle cannot be 270.

        print('')
        print('AFTER')
        broke = False
        for index in indices:

            state = self.get_state((index,))
            node = self.index_to_node[index]
            angle = None
            if self.is_collapsed(state):
                try:
                    angle = self.get_tile((index,))
                except:
                    angle = 'CONTRADICTION'
                    broke = True
            print('    index:', index, 'node:', node, self.is_collapsed(state), '->', state, angle)
        print('')

        if broke:
            self.debug()
            raise

        print('NODE END')

        # print('3:')
        # self.debug()
        # print('END 3')

        return propagate

    def get_min_entropy_coords_offset(self):
        return self.block_sizes + super().get_min_entropy_coords_offset()

    def propagate(self, coords):

        print('\nPROPAGATE:', coords)

        stack = [coords]
        while stack:

            propagate = set()
            cur_coords = stack.pop()
            print('\nLOOP index:', cur_coords[0], 'node:', self.index_to_node[cur_coords[0]], 'block:', self.index_to_block[cur_coords[0]])

            block = self.index_to_block[cur_coords[0]]
            next_coords_by_block = self.propagate_by_block(block)
            #propagate.update(next_coords_by_block)

            start, stop = self.block_to_index_range[block]
            block_slice = slice(start, stop)
            block_state = self.get_state((block_slice,))
            for index in range(np.size(block_state, axis=1)):
                index = start + index
                node = self.index_to_node[index]
                next_coords_by_node = self.propagate_by_node(index, node)
                propagate.update(next_coords_by_node)

            stack.extend((i,) for i in propagate)

            #print('\nBLOCK NEXT COORDS:', next_coords_by_block)
            #print('NODE NEXT COORDS:', next_coords_by_node)
            print('STACK:', stack)

            # Assert block sum is 360.
            for block_index, block in enumerate(self.block_g):
                start, stop = self.block_to_index_range[block]
                block_slice = slice(start, stop)
                block_state = self.get_state((block_slice,))

                total = 0
                for index in range(np.size(block_state, axis=1)):
                    state = block_state[(slice(None), index)]
                    if self.is_collapsed(state):
                        total += self.get_tile((start + index,))
                    else:
                        break
                else:
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
            node = self.index_to_node[index]
            block = self.index_to_block[index]
            state = self.get_state((index,))
            angle = None
            if self.is_collapsed(state):
                try:
                    angle = self.get_tile((index,))
                except:
                    angle = 'CONTRADICTION'
            results[(block, node)] = angle, state, index

        for block, node in sorted(results, key=lambda bn: len(bn[0])):
            angle, state, index = results[block, node]
            print('    ', 'index:', index, 'node:', node, 'angle:', angle, 'block:', block, '->', state)