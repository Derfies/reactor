import enum
import random
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

    def _calculate_angle_permutations(self):

        # Warning! These edges aren't guaranteed to be contiguous.
        poss_angles = []
        common_edges = self.layout.get_common_edges(self.data)
        for node in nx.dfs_preorder_nodes(self.data):#self.data.nodes2:
            state_idx = len(filter(lambda edge: node in edge, common_edges))
            state = NodeState(state_idx)
            if state == NodeState.known:
                poss_angles.append([self.layout.get_explementary_angle(node)])
            elif state == NodeState.unknown:
                poss_angles.append(self.layout.get_possible_angles(node))
            elif state == NodeState.free:
                poss_angles.append(list(Angle))
        all_angle_perms = set(it.product(*poss_angles))
        return filter(lambda x: sum(x) == 360, all_angle_perms)

    def _calculate_face_permutations(self, angle_perms, start_dir):

        # There *must* be a common node already in the layout.
        offset = self.layout.nodes[self.data.get_source_edge()[0]][POSITION]

        # TODO: Replace with get_edge_attributes
        lengths = [
            self.layout.edges.get(edge, {}).get(LENGTH)
            for edge in self.data.edges_reverse()
        ]
        ofaces = []
        for angles in angle_perms:

            oface = OrthogonalFace(
                list(self.data.edges_forward()),
                angles,
                lengths[:],
                start_dir,
                offset
            )
            ofaces.append(oface)

            for dir_, opp_dir in (Direction.xs(), Direction.ys()):

                # Define two sides - one with the shorter proposed length and
                # one with the longer proposed length.
                min_side, max_side = oface.sides[opp_dir], oface.sides[dir_]
                if max_side.proposed_length < min_side.proposed_length:
                    min_side, max_side = max_side, min_side

                print '\n    Axis:', dir_, opp_dir

                # If one of the sides has a known length then we must use that
                # length
                max_length = max_side.proposed_length
                if min_side.state == SideState.known:
                    max_length = min_side.length
                elif max_side.state == SideState.known:
                    max_length = max_side.length
                print '    max_length:', max_length

                # If the min side is unknown, split the remainder and divide it
                # amongst the edges.
                if min_side.state == SideState.unknown:
                    min_side_edge = (
                                                max_length - min_side.known_length) / float(
                        min_side.num_unknown_edges)
                    for edge_idx in min_side.indices:
                        oface.lengths[edge_idx] = oface.lengths[
                                                      edge_idx] or min_side_edge

                # print '    min_side_edges:'
                # for edge_idx in min_side.indices:
                #     print '    ', edge_idx, oface[edge_idx], oface.lengths[
                #         edge_idx]

                # If the max side is unknown, split the remainder and divide it
                # amongst the edges.
                if max_side.state == SideState.unknown:
                    max_side_edge = (
                                                max_length - max_side.known_length) / float(
                        max_side.num_unknown_edges)
                    for edge_idx in max_side.indices:
                        oface.lengths[edge_idx] = oface.lengths[
                                                      edge_idx] or max_side_edge

                # print '    max_side_edges:'
                # for edge_idx in max_side.indices:
                #     print '    ', edge_idx, oface[edge_idx], oface.lengths[edge_idx]


        return ofaces

    def get_permutations(self):

        angle_perms = self._calculate_angle_permutations()

        # Get starting edge direction.
        #start_dir = Direction.up
        common_edges = self.layout.get_common_edges(self.data)
        #if common_edges:
        edge = common_edges[0]
        rev_dir = self.layout.edges[edge][DIRECTION]
        start_dir = Direction.opposite(rev_dir)

        print '    start node:', self.data.get_source_edge()[0]
        print '    common_edges:', common_edges
        print '    start dir:', start_dir

        ofaces = self._calculate_face_permutations(angle_perms, start_dir)

        return self.to_faces(ofaces)

    def to_faces(self, ofaces):

        # TODO: Remove this function once face class has been fixed up...
        # TODO: Turn face into graph...
        rtn = []
        for face in ofaces:
            g = nx.DiGraph()

            print face, list(face), type(face)

            # Merge edges into the graph.
            g.add_edges_from(face)

            # Merge node data into the graph.
            for node_idx, node in enumerate(face.nodes):
                g.nodes[node][ANGLE] = face.angles[node_idx]
                g.nodes[node][POSITION] = face.positions[node_idx]

                # print '    node:', node, g.nodes[node][POSITION]

            # Merge edge data into the graph.
            for edge_idx, edge in enumerate(face):
                g.edges[edge][LENGTH] = face.lengths[edge_idx]
                g.edges[edge][DIRECTION] = face.directions[edge_idx]
            rtn.append(g)

        random.shuffle(rtn)
        return rtn

    def update_layout(self, g):

        # Merge node data into the graph.
        # TODO: Clean this up!
        node_attrs = {}
        for node in nx.dfs_preorder_nodes(g):
            new = {g: g.nodes[node].pop(ANGLE)}
            old = self.layout.nodes.get(node, {}).get(ANGLE, {})
            old.update(new)
            node_attrs[node] = {ANGLE: old}
        super(CyclicBlock, self).update_layout(g)
        nx.set_node_attributes(self.layout, node_attrs)