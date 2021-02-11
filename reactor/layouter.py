import abc
import itertools as it
import numpy as np
import random

import networkx as nx

from reactor.blocks.blockgraph import BlockGraph
from reactor.blocks.edgeblock import EdgeBlock
from reactor.blocks.faceblock import FaceBlock
from reactor.blocks.rootblock import RootBlock
from reactor.faceanalysis import FaceAnalysis
from reactor.const import Angle
from reactor.layouters.facelayouter import NodeState


class WavefunctionBase(metaclass=abc.ABCMeta):

    def __init__(self):
        weights = [1, 1, 1]

        self.weights = np.array(weights, dtype=np.float64)

    #@property
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
        index = np.argmin(entropy)
        return np.unravel_index(index, entropy.shape)

    def collapse_to_tile(self, coords, tile):
        states = self.wave[(slice(None), *coords)]
        states[:] = False
        index = self.tiles.index(tile)
        states[index] = True

    def collapse(self, coords):
        states = self.wave[(slice(None), *coords)]
        weighted_states = self.weights * states
        weighted_states /= weighted_states.sum()
        index = np.random.choice(self.weights.size, p=weighted_states)
        states[:] = False
        states[index] = True

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
            coords = self.get_min_entropy_coords()
            self.collapse(coords)
            self.propagate(coords)
            raise


class AngleWavefunction(WavefunctionBase):

    """
    Use this to replace the current cyclic layouter, however it doesn't so
    edge lengths.

    Do we care? What does that mean?

    """

    def __init__(self, g, block_g):
        super().__init__()

        self.g = g
        self.block_g = block_g

        self.wave_to_block = []
        self.block_sizes = []
        self.block_edges = []
        self.block_ranges = []
        num_angles = 0

        self.wave_to_node = []
        self.node_to_block = {}
        self.node_to_waves = {}
        m = 0
        wave_index = 0
        for block_index, block in enumerate(self.block_g):
            nodes = list(block.nodes)
            num_angles += len(block)
            self.wave_to_block.extend([block] * len(block))
            self.block_sizes.extend([len(block)] * len(block))
            for i, edge in enumerate(block.edges_forward):
                self.block_edges.append(edge)
                node = nodes[i]
                self.wave_to_node.append(node)
                self.node_to_block.setdefault(node, set()).add(block)
                self.block_ranges.append((m, m + len(block)))
                self.node_to_waves.setdefault(node, set()).add(wave_index)

                wave_index += 1
            m += len(block)

        self.tiles = list(Angle)
        print('tiles:', self.tiles)

        # Wave shape is 2D - dim 1 is the number of angle variants and dim 2 is
        # how many angles we have.
        shape = (num_angles,)
        final_shape = (len(self.tiles),) + shape
        self.wave = np.ones(final_shape, dtype=bool)

        # We can collapse some angles based on a few assumptions already.
        # TODO: Can collapse nodes whose incident value equals their number of
        # faces... I think.
        propagate_coords = []
        outside_index = self.tiles.index(Angle.OUTSIDE)
        straight_index = self.tiles.index(Angle.STRAIGHT)
        start = 0
        for block_index, block in enumerate(self.block_g):
            block_len = len(block)
            if block_len < 6:
                stop = start + block_len
                wave_index = (slice(None), slice(start, stop))
                block_wave = self.wave[wave_index]
                block_wave[:][outside_index] = False
                if block_len < 5:
                    block_wave[:][straight_index] = False

                for x in range(start, stop):
                    propagate_coords.append((x,))
            start += block_len

        # DEBUG
        # start = 0
        # for block_index, block in enumerate(self.block_g):
        #     block_len = len(block)
        #     stop = start + block_len
        #     wave_index = (slice(None), slice(start, stop))
        #     block_wave = self.wave[wave_index]
        #     print('')
        #     print(f'block ({len(block)}):', block)
        #     print('block wave:\n', block_wave)
        #     start += block_len

        for coord in propagate_coords:
            self.propagate(coord)

    def get_min_entropy_coords_offset(self):
        return self.block_sizes + super().get_min_entropy_coords_offset()

    def get_tile(self, coords):
        states = self.wave[(slice(None), *coords)]
        nonzero = np.nonzero(states)
        indices = nonzero[0]
        assert indices.size == 1, 'Cannot resolve the tile'
        return self.tiles[indices[0]]

    def propagate(self, coords):

        print('')
        print('PROPAGATE:', coords)

        stack = [coords]

        while len(stack) > 0:
            cur_coords = stack.pop()

            angle_index = cur_coords[0]
            block = self.wave_to_block[angle_index]

            print('    coords:', cur_coords)
            print('    block:', block)

            node = self.wave_to_node[angle_index]
            blocks = self.node_to_block[node]
            start, stop = self.block_ranges[angle_index]
            wave_index = (slice(None), slice(start, stop))
            block_wave = self.wave[wave_index]
            is_collapsed = self.is_collapsed(block_wave)

            # TODO: If only one unknown angle remains for a block we can guess
            # what it is.

            neighbors = list(self.g.neighbors(node))
            if len(neighbors) == 2 and is_collapsed:
                print('    ******* CAN PROPAGATE HERE!')
                angle = self.get_tile(cur_coords)
                print('    angle:', angle)
                print('    node_to_waves:', self.node_to_waves[node])
                for wave in self.node_to_waves[node]:

                    adj_block = self.wave_to_block[wave]
                    if adj_block == block:
                        continue
                    print('        wave:', wave)
                    print('        wave node:', self.wave_to_node[wave])
                    print('        wave block:', adj_block)
                    total = angle
                    other = Angle(180 - (360 - total))
                    print('        other:', other)

                    self.collapse_to_tile((wave,), other)
                    stack.append((wave,))


class Layouter(object):

    def __init__(self, g, map_):
        self._g = g
        self._map = map_

    @property
    def g(self):
        return self._g

    def _sort_nodes(self, nodes):
        """
        Sort criteria:
        - Prioritise faces
        - Priortise smaller faces
        - Sorted tuple

        """
        return sorted(nodes, key=lambda n: (len(n) < 3, len(n), sorted(n)))

    def bfs_tree(self, g, source, reverse=False, depth_limit=None, sort_neighbors=None):
        t = BlockGraph()
        t.add_node(source)
        edges_gen = nx.bfs_edges(
            g,
            source,
            reverse=reverse,
            depth_limit=depth_limit,
            sort_neighbors=sort_neighbors,
        )
        t.add_edges_from(edges_gen)
        return t

    # TODO: Make this class the actual quotient graph and make this a class
    # method.
    def get_block_graph(self):

        # Split the input graph into biconnected components. Each biconn will
        # become a node in the block graph.
        g = nx.Graph()

        # Build nodes.
        biconns = list(nx.biconnected_components(self.g))
        for biconn in biconns:
            sg = self.g.subgraph(biconn)
            if len(biconn) < 3:
                g.add_node(EdgeBlock(sg))
            else:
                for face in FaceAnalysis(sg).get_faces():
                    fsg = self.g.subgraph(face)
                    g.add_node(FaceBlock.from_path(face, fsg))

        # Build edges.
        edges = filter(lambda x: x[0].is_adjacent(x[1]), it.combinations(g, 2))
        g.add_edges_from(edges)

        # print('num_blocks:', len(g))
        # for n in g:
        #     print('block:', n)

        # Find path from N1 to N13.
        #print(list(self.g))
        #paths = nx.all_shortest_paths(self.g, 'N1', 'N13')
        my_path = [
            'N2',
            'N1',
            'N5',
            'N4',
            'N6',
            'N39',
            'N41',
            'N33',
            'N34',
            'N29',
            'N30',
            'N7',
            'N14',
            'N12',
            'N19',
            'N21',
            'N23',
            'N24',
            'N43',
            'N44',
            'N47',
            'N48',
            'N50',
            'N51'
        ]
        for path in (my_path,):

            #print('\npath:', path)

            # Find the components that lie on this path.
            # for block in g:
            #     #print('biconn:', biconn)
            #     if set(block) & set(path):
            #         print('    overlap:', type(block), list(block))

            # NEED TO ORIENT THE PATH SO THE RELATIVITY OF THE ANGLES MAKES
            # SENSE.

            # ORIENT THE GRAPH...? Would that make things easier?

            # Find the possible angle of every node on the path. Remember that
            # these angles are relative to each other - not the world, eg STRAIGHT
            # means continue along the vector of the previous edge. The first
            # and last node angles can be anything until we figure out what
            # these nodes connect to.
            #
            # If an edge incident to a node forms the border between two faces
            # that also share edges with the path then we know the angle of the
            # node must be straight or outside.
            #
            # If a node has four incident edges, we check if the path belongs
            # to the same face. If the path falls on the same face then the
            # angle is either inside or outside, depending on the path direction.
            # If the path falls on different faces then the angle is straight.
            wf = AngleWavefunction(self.g, g)
            #print(wf.wave.shape)

            #wf.run()

            # DEBUG
            start = 0
            for block_index, block in enumerate(wf.block_g):
                block_len = len(block)
                stop = start + block_len
                wave_index = (slice(None), slice(start, stop))
                block_wave = wf.wave[wave_index]
                print('')
                print(f'block ({len(block)}):', block)
                print('block wave:\n', block_wave)
                start += block_len


            raise
            #prev_node = path[0]
            #for i, node in enumerate(path[:-1]):
            path = nx.path_graph(path, create_using=nx.DiGraph)#nx.DiGraph(self.g.subgraph(path))
            print('path:', list(path))
            for node in path:
                #next_node = path[i + 1]
                print('\n    node:', node)

                # Get incident edges and reorder.
                # incidents = self.g.in_edges(node) + self.g_out_edges(node)
                # for i, incident in enumerate(incidents):
                #     if incident not in path:
                #         incidents[i] = tuple(reversed(list(incident)))


                #num_incidents = len(incidents)
                #state = None
                #if num_incidents == 4:
                #    state = NodeState.KNOWN

                # Len or 1 or 2.
                # incident_edges_on_path = [
                #     incident
                #     for incident in incidents
                #     if set(path).issuperset(set(incident))
                # ]
                # from itertools import tee
                # def pairwise(iterable):
                #     "s -> (s0,s1), (s1,s2), (s2, s3), ..."
                #     a, b = tee(iterable)
                #     next(b, None)
                #     return zip(a, b)


                # *************************

                # If num incident face blocks is 1, then the node is on an edge
                # with the external face and can have angles of 90, 0, -90
                # degrees (providing the adjoining face has the number of verts
                # to allow this).

                # If the num incident face blocks is 2, then the node is on an
                # edge between two interior faces and can have angles of 90, 0,
                # -90 degrees (providing the adjoining face has the number of
                # verts to allow this).

                # If the num incident face blocks is 3, then the node is on an
                # edge between three interior faces and can have angles of 90,
                # 0 or -90 and 0. If the path is along two edges of the same
                # face then there are two possible angles (the sign coming from
                # turning left or right which is divined from the winding order
                # of the adjoining face). Look to the number of verts of each
                # adjoining face to see what angles they will allow.

                # If the num incident face blocks is 4, then we should be able
                # to divine exactly which angle the node must be. If the path
                # is contained on the same face then the angle is either 90 or
                # -90 depending on the winding order. If the path is along
                # different faces then the angle is 0.


                # TODO: If in_edge or out_edge is None then the angle could be
                # anything, potentially even a hair-pin reflex angle.
                in_edge = next(iter(path.in_edges(node)), None)
                out_edge = next(iter(path.out_edges(node)), None)
                print('        in_edge:', in_edge)
                print('        out_edge:', out_edge)

                # Find the cycle that lies on the path if there is one.
                node_blocks = [block for block in g if node in block]
                for block in node_blocks:

                    # Can divine which angles we need by whether the face is on
                    # the left or right side of the path.
                    edges_forward = set(block.edges_forward)
                    edges_reverse = set(block.edges_reverse)
                    if edges_forward.issuperset({in_edge, out_edge}):
                        angles = [Angle.OUTSIDE, Angle.STRAIGHT, Angle.INSIDE]
                        break
                    elif edges_reverse.issuperset({in_edge, out_edge}):
                        angles = [Angle.INSIDE, Angle.STRAIGHT, Angle.OUTSIDE]
                        break

                else:

                    # The only reason we wouldn't have a block on the path is
                    # when there are 4 incident edges and the path goes through
                    # the middle.
                    angles = [Angle.STRAIGHT]
                    block = None

                num_incident_edges = len(self.g.edges(node))
                max_num_angles = 5 - num_incident_edges
                if block is not None:

                    if len(block) == 4:
                        max_num_angles = min(max_num_angles, 1)
                        #print(f'    reduced max_num_angles to: {max_num_angles} because of 4 sided')
                    elif len(block) == 5:
                        max_num_angles = min(max_num_angles, 2)
                        #print(f'    reduced max_num_angles to: {max_num_angles} because of 5 sided')



                        # Get the block(s) on the other side.
                        # If one of the blocks on the other side is 4, then it can't
                        # be an "inward" angle.
                        other_blocks = set(node_blocks) - set([block])
                        #for o_block in other_blocks:
                            #print('    o_block:', len(o_block))

                        if other_blocks:
                            lens = [len(b) for b in other_blocks]
                            min_len = min(lens)
                            #print('    min len:', min_len)
                            if min_len == 4 or min_len == 5:
                                angles.pop(0)
                                max_num_angles = -1


                #print('    max num angles:', max_num_angles)

                # Trim off the number of possible angles by how many incident
                # edges there are.
                angles = angles[:max_num_angles]
                #print('    angles:', angles)








                # New impl.

                # Split blocks into those on the left of the line and those on
                # the right of the line.
                lefts, rights, orphans = [], [], []
                for block in node_blocks:
                    if set(block.edges_forward) & {in_edge, out_edge}:
                        lefts.append(block)
                    elif set(block.edges_reverse) & {in_edge, out_edge}:
                        rights.append(block)
                    else:
                        orphans.append(block)

                assert not set(lefts) & set(rights), 'cant be on both sides, buddy'
                assert len(orphans) < 2, 'Should be max 1 orphan'
                if orphans:
                    assert len(lefts) != len(rights), 'Shouldnt have an orphan plus equal lefts and rights'

                # If there are any blocks unaccounted for, these are added to
                # the side with more blocks (ie a corner)
                if orphans:
                    (lefts if len(lefts) > len(rights) else rights).extend(orphans)
                    #print('   #### added orphan')

                print('    left', len(lefts), [str(b) for b in lefts])
                print('    right', len(rights), [str(b) for b in rights])
                # print('    orphans', len(orphans), [str(b) for b in orphans])

                # If there's more than one block on the left side, we can't turn
                # outwards.
                angles = set(list(Angle))
                if len(rights) > 1:
                    angles.discard(Angle.INSIDE)
                    if len(rights) == 2 and max([len(right) for right in rights]) == 4:
                        angles.discard(Angle.OUTSIDE)
                if len(lefts) > 1:
                    angles.discard(Angle.OUTSIDE)
                    if len(lefts) == 2 and max([len(left) for left in lefts]) == 4:
                        angles.discard(Angle.INSIDE)

                # If there are more than two blocks on the left or the right,
                # we can't go straight.
                if len(lefts) > 2 or len(rights) > 2:
                    angles.discard(Angle.STRAIGHT)

                # If there is a single block on the right and it's a square,
                # we HAVE to turn right.
                if len(lefts) == 1:
                    left_block = lefts[0]
                    is_on_path = set(left_block.edges_forward).issuperset({in_edge, out_edge})
                    if is_on_path:
                        print('    is_on_path:', is_on_path)
                        if len(left_block) < 6:
                            angles.discard(Angle.INSIDE)
                        if len(left_block) < 5:
                            angles.discard(Angle.STRAIGHT)

                # If there is a single block on the right and it's a square,
                # we HAVE to turn right.
                if len(rights) == 1:
                    right_block = rights[0]
                    is_on_path = set(right_block.edges_reverse).issuperset({in_edge, out_edge})
                    if is_on_path:
                        print('    is_on_path:', is_on_path)
                        if len(right_block) < 6:
                            angles.discard(Angle.OUTSIDE)
                        if len(right_block) < 5:
                            angles.discard(Angle.STRAIGHT)

                # REMAINING:
                # Abstract the above.
                # Fix issue when we have 4 incident edges but only 3 blocks
                # See if the N44 issue is systemic
                # Test non-cyclic blocks

                # Both 4 and 5 sided quads can only ever be laid out as a square
                # Squares decrease this thing I'm going to call "flexibility"

                print('    ANGLES:', angles)

                assert angles, 'Need at least one angle'




                continue



        return


        # Find root node.
        sorted_nodes = self._sort_nodes(g)
        root = sorted_nodes[0]

        # Put a super root behind the root node. This will place the very first
        # node at the origin.
        super_root = RootBlock(self.g.subgraph([sorted(root)[0]]))
        g.add_edge(super_root, root)

        # Orient graph. Sort neighbours so that faces are visited first from
        # smallest to largest, then other biconns.
        g = self.bfs_tree(g, super_root, sort_neighbors=self._sort_nodes)

        # Sort nodes.
        for node in g:
            p_node = g.parent(node)
            node.sort(p_node)

        return g

    def bfs(self, g):
        blocks = list(g)
        #print('blocks:')
        #for b in blocks:
        #    #print('    ->', b)

        i = 0
        while i < len(blocks):

            layouter = g.get_layouter(blocks[i])
            if layouter.done:
                #print('SKIPPING AS DONE:', blocks[i])
                i += 1
                continue

            #print('process ->', i, blocks[i], 'parent:', g.parent(blocks[i]))
            if not layouter.permutations:# is None:
                #print('    creating new perms')
                #try:
                layouter.permutations = layouter.get_permutations(self._map.layout)
                # except:
                #     from reactor import utils
                #     pos = nx.get_node_attributes(self.layout, POSITION)
                #     utils.draw_graph(self.layout, pos)
                #     raise
                random.shuffle(layouter.permutations)
            #else:
                #print('    using existing perms')

            while layouter.permutations:
                perm = layouter.permutations.pop(0)
                if not layouter.can_lay_out(perm, self._map):
                    #print('    FAILED:', nx.get_node_attributes(perm, POSITION))
                    continue
                layouter.add_to_layout(perm, self._map.layout)
                #print('    SUCCESS:', list(perm.edges), nx.get_node_attributes(perm, POSITION))
                layouter.done = True

                i += 1
                break
            else:

                # Move the cursor back to the parent.
                parent = g.parent(blocks[i])
                #print('BACKTRACK:', blocks[i], 'TO:', parent)
                while blocks[i] != parent:
                    #print('    REWIND:', blocks[i], i)
                    i -= 1

                # Mark all blocks under the parent as not done and remove
                # their permutations.
                j = i
                while j < len(blocks):
                    olayouter = g.get_layouter(blocks[j])
                    if olayouter.done:
                        olayouter.done = False
                        if blocks[j] != blocks[i]:
                            olayouter.permutations.clear()
                            #print('    REMOVE PERMS:', blocks[j])
                    j += 1

                # Remove the failed blocks from the layout.
                rem_blocks = nx.dfs_tree(g, blocks[i])
                for block in rem_blocks:
                    olayouter = g.get_layouter(block)
                    olayouter.remove_from_layout(self._map.layout)

    def run(self):
        bg = self.get_block_graph()
        return
        self.bfs(bg)
        print('complete:', len(self.g) == len(self._map.layout))
        print('remainging:', set(self.g) - set(self._map.layout))
