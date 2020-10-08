import enum
import itertools as it

import networkx as nx

from reactor.blocks.blockbase import BlockBase
from reactor.const import POSITION, DIRECTION, Direction, LENGTH, SideState, ANGLE, Angle
from reactor.orthogonalface import OrthogonalFace


class NodeState(enum.IntEnum):

    unknown = 0
    free = 1
    known = 2


class CyclicBlock(BlockBase):

    def __str__(self):
        return self.__class__.__name__ + ' [' + str(list(self.data.edges)) + ']'

    def get_angle_permutations(self):

        # Warning! These edges aren't guaranteed to be contiguous.
        angle_perms = {}
        common_edges = tuple(self.layout.get_common_edges(self.data))
        for node in nx.dfs_preorder_nodes(self.data):
            state_idx = len([e for e in common_edges if node in e])
            state = NodeState(state_idx)
            if state == NodeState.known:
                angle_perms[node] = (self.layout.get_explementary_angle(node),)
            elif state == NodeState.unknown:
                angle_perms[node] = self.layout.get_possible_angles(node)
            elif state == NodeState.free:
                angle_perms[node] = tuple(Angle)

        # TODO: Check it this is ok...
        # TODO: Not removing duplicates!
        keys = angle_perms.keys()
        vals = angle_perms.values()
        for instance in it.product(*vals):
            if sum(instance) == 360:
                yield dict(zip(keys, instance))

    def get_face_permutations(self, start_dir):

        # There *must* be a common node already in the layout.
        offset = self.layout.nodes[self.data.get_source_edge()[0]][POSITION]

        # Pull out known edge lengths from the layout.
        lengths = {
            edge: self.layout.edges.get((edge[1], edge[0]), {}).get(LENGTH)
            for edge in self.data.edges
        }

        ofaces = []
        for angles in self.get_angle_permutations():

            oface = OrthogonalFace(self.data, angles, lengths, start_dir, offset)
            ofaces.append(oface)

            for dir_, opp_dir in (Direction.xs(), Direction.ys()):

                # Define two sides - one with the shorter proposed length and
                # one with the longer proposed length.
                min_side, max_side = oface.sides[opp_dir], oface.sides[dir_]
                if max_side.proposed_length < min_side.proposed_length:
                    min_side, max_side = max_side, min_side

                # If one of the sides has a known length then we must use that
                # length
                max_length = max_side.proposed_length
                if min_side.state == SideState.known:
                    max_length = min_side.length
                elif max_side.state == SideState.known:
                    max_length = max_side.length

                # If the min side is unknown, split the remainder and divide it
                # amongst the edges.
                if min_side.state == SideState.unknown:
                    min_side_edge = (max_length - min_side.known_length) / float(min_side.num_unknown_edges)
                    for edge in min_side.g.edges:
                        oface.edges[edge][LENGTH] = min_side.g.edges[edge][LENGTH] or min_side_edge

                # If the max side is unknown, split the remainder and divide it
                # amongst the edges.
                if max_side.state == SideState.unknown:
                    max_side_edge = (max_length - max_side.known_length) / float(max_side.num_unknown_edges)
                    for edge in max_side.g.edges:
                        oface.edges[edge][LENGTH] = max_side.g.edges[edge][LENGTH] or max_side_edge

            # Final node positions.
            for node, pos in oface.get_node_positions().items():
                oface.nodes[node][POSITION] = pos

        return ofaces

    def get_permutations(self):
        edge = next(self.layout.get_common_edges(self.data))
        dir_ = Direction.opposite(self.layout.edges[edge][DIRECTION])
        return self.get_face_permutations(dir_)

    def update_layout(self, g):

        # Per node angle data is a dict that must be updated or else clobbered.
        for node in g:
            attr = self.layout.nodes.get(node, {}).pop(ANGLE, {})
            attr.update({g: g.nodes[node].pop(ANGLE)})
            g.nodes[node][ANGLE] = attr
        super(CyclicBlock, self).update_layout(g)