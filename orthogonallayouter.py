import copy
import itertools as it

import networkx as nx

from const import Direction, NodeState, ANGLE, LENGTH, SideState, Angle, DIRECTION
from orthogonalgraph import OrthogonalGraph
from orthogonalface import OrthogonalFace


class OrthogonalLayouter(object):

    def __init__(self, faces):
        self.faces = faces

    def _get_next_walk_direction(self, g, face, indent):

        # Pick an edge-walk direction. If there's a common edge we need to use
        # that same edge's direction in order for the faces to join.
        walk_dir = Direction.up
        rev_edge = tuple(reversed(face[0]))
        if rev_edge in g.edges:
            rev_walk_dir = g.edges[rev_edge][DIRECTION]
            walk_dir = Direction.opposite(rev_walk_dir)
        return walk_dir

    def _permute_face_angles(self, g, face, indent):

        print ' ' * indent, 'Permute angles:'

        # Warning! These edges aren't guaranteed to be contiguous.
        poss_angles = []
        common_edges = g.get_common_edges(face)
        for node in face.nodes:
            state_idx = len(filter(lambda edge: node in edge, common_edges))
            state = NodeState(state_idx)
            if state == NodeState.known:
                #try:

                angles = []
                try:
                    angles.append(g.get_explementary_angle(node))
                except ValueError:
                    pass
                poss_angles.append(angles)
                # except:

                #     print 'FAILED:', node#, nx.get_node_attributes(g, ANGLE).get(node)
                #     self.debug = g
                #     raise
            elif state == NodeState.unknown:
                poss_angles.append(g.get_possible_angles(node))
            elif state == NodeState.free:
                poss_angles.append(list(Angle))
            print ' ' * (indent + 2), node, state, poss_angles[-1], nx.get_node_attributes(g, ANGLE).get(node)
        all_angle_perms = set(it.product(*poss_angles))
        return filter(lambda x: sum(x) == 360, all_angle_perms)

    def permute_layouts(self, g, face, indent):

        angle_perms = self._permute_face_angles(g, face, indent + 2)
        walk_dir = self._get_next_walk_direction(g, face, indent + 2)

        # Turn each set of
        ofaces = []
        for angles in angle_perms:

            lengths = [g.edges.get(edge, {}).get(LENGTH) for edge in face]
            oface = OrthogonalFace(face.edges, angles, lengths, walk_dir)
            ofaces.append(oface)

            bar = zip(oface.nodes, oface.angles)
            # print ' ' * (indent + 2), 'Angles:', bar

            missing_lengths = {}
            for dir_, opp_dir in (Direction.xs(), Direction.ys()):

                # Define two sides - one with the shorter proposed length and
                # one with the longer proposed length.
                min_side, max_side = oface.sides[opp_dir], oface.sides[dir_]
                if max_side.proposed_length < min_side.proposed_length:
                    min_side, max_side = max_side, min_side

                # print ' ' * (indent + 6), 'Axis:', dir_, opp_dir

                max_length = max_side.proposed_length

                if min_side.state == SideState.known:
                    max_length = min_side.length
                elif max_side.state == SideState.known:
                    max_length = max_side.length
                # print ' ' * (indent + 8), 'max_length:', max_length

                if min_side.state == SideState.unknown:
                    min_side_edge = (
                                                max_length - min_side.known_length) / float(
                        min_side.num_unknown_edges)
                    for edge_idx in min_side.indices:
                        oface.lengths[edge_idx] = oface.lengths[
                                                      edge_idx] or min_side_edge

                if max_side.state == SideState.unknown:
                    max_side_edge = (
                                                max_length - max_side.known_length) / float(
                        max_side.num_unknown_edges)
                    for edge_idx in max_side.indices:
                        oface.lengths[edge_idx] = oface.lengths[
                                                      edge_idx] or max_side_edge

                # print ' ' * (indent + 8), 'max_side_edge:', [oface.lengths[edge_idx] for edge_idx in max_side.indices]

        return ofaces

    def _process_face(self, face_idx, g, indent):

        face = self.faces[face_idx]
        print ''
        print ' ' * indent, 'Process face:', face

        layouts = self.permute_layouts(g, face, indent)
        print ' ' * indent, 'Num layouts:', len(layouts)

        for i, layout in enumerate(layouts):

            # Need to deep copy the graph or else attribute dicts are polluted
            # between copies.
            g_copy = copy.deepcopy(g)
            g_copy.add_face(layout)

            # Find adjoining faces.
            if face_idx < len(self.faces) - 1:
                self._process_face(face_idx + 1, g_copy, indent + 4)
            else:
                self.graphs.append(g_copy)


    def run(self):
        self.graphs = []
        self._process_face(0, OrthogonalGraph(), 0)