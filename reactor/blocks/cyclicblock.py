import enum
import itertools as it

import networkx as nx

from reactor.blocks.blockbase import BlockBase
from reactor.const import POSITION, DIRECTION, Direction, LENGTH, ANGLE, Angle
from reactor.orthogonalface import OrthogonalFace, SideState


class NodeState(enum.IntEnum):

    UNKNOWN = 0
    FREE = 1
    KNOWN = 2


class CyclicBlock(BlockBase):

    def __str__(self):
        return self.__class__.__name__ + ' [' + str(list(self.data.edges)) + ']'

    def get_angle_permutations(self, layout):

        # Warning! These edges aren't guaranteed to be contiguous.
        angle_perms = {}
        common_edges = tuple(layout.get_common_edges(self.data))
        for node in nx.dfs_preorder_nodes(self.data):
            state_idx = len([e for e in common_edges if node in e])
            state = NodeState(state_idx)
            if state == NodeState.KNOWN:
                angle_perms[node] = (layout.get_explementary_angle(node),)
            elif state == NodeState.UNKNOWN:
                angle_perms[node] = layout.get_possible_angles(node)
            elif state == NodeState.FREE:
                angle_perms[node] = tuple(Angle)

        # TODO: Check it this is ok...
        # TODO: Not removing duplicates!
        keys = angle_perms.keys()
        vals = angle_perms.values()
        for instance in it.product(*vals):
            if sum(instance) == 360:
                yield dict(zip(keys, instance))

    def get_face_permutations(self, start_dir, layout):

        # There *must* be a common node already in the layout.
        offset = layout.nodes[self.data.get_source_edge()[0]][POSITION]

        # Pull out known edge lengths from the layout.
        lengths = {
            edge: layout.edges.get((edge[1], edge[0]), {}).get(LENGTH)
            for edge in self.data.edges
        }

        ofaces = []
        for angles in self.get_angle_permutations(layout):

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
                if min_side.state == SideState.KNOWN:
                    max_length = min_side.length
                elif max_side.state == SideState.KNOWN:
                    max_length = max_side.length

                # If the min side is unknown, split the remainder and divide it
                # amongst the edges.
                if min_side.state == SideState.UNKNOWN:
                    min_side_edge = (max_length - min_side.known_length) / float(min_side.num_unknown_edges)
                    for edge in min_side.g.edges:
                        oface.edges[edge][LENGTH] = min_side.g.edges[edge][LENGTH] or min_side_edge

                # If the max side is unknown, split the remainder and divide it
                # amongst the edges.
                if max_side.state == SideState.UNKNOWN:
                    max_side_edge = (max_length - max_side.known_length) / float(max_side.num_unknown_edges)
                    for edge in max_side.g.edges:
                        oface.edges[edge][LENGTH] = max_side.g.edges[edge][LENGTH] or max_side_edge

            # Final node positions.
            for node, pos in oface.get_node_positions().items():
                oface.nodes[node][POSITION] = pos

        return ofaces

    def get_permutations(self, layout):
        edge = next(layout.get_common_edges(self.data))
        dir_ = Direction.opposite(layout.edges[edge][DIRECTION])
        return self.get_face_permutations(dir_, layout)

    def update_layout(self, perm, layout):

        # Per node angle data is a dict that must be updated or else clobbered.
        for node in perm:
            attr = layout.nodes.get(node, {}).pop(ANGLE, {})
            attr.update({perm: perm.nodes[node].pop(ANGLE)})
            perm.nodes[node][ANGLE] = attr
        super(CyclicBlock, self).update_layout(perm, layout)
