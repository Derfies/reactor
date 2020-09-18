import copy
import enum
import itertools as it

import networkx as nx
import matplotlib.pyplot as plt

from ..vector import Vector2
from ..const import Direction, ANGLE, LENGTH, SideState, Angle, DIRECTION, POSITION
from ..orthogonalgraph import OrthogonalGraph
from ..orthogonalface import OrthogonalFace
from layouterbase import LayouterBase
from ..embeddedbiconngraph import EmbeddedBiconnGraph


class NodeState(enum.IntEnum):

    unknown = 0
    free = 1
    known = 2


class CyclicLayouter(LayouterBase):

    def __init__(self, g, other=None, start_node=None):
        super(CyclicLayouter, self).__init__()

        # Try to run the planar layout on the bicon component. If this fails
        # show the layout for debug.
        bg = EmbeddedBiconnGraph(g)
        try:
            bg.run()
        except nx.exception.NetworkXException:
            nx.draw_networkx(bg.g, bg.pos)
            plt.show()
            raise

        #self.layouter = CyclicLayouter(bg.faces)
        #self.layouter.run()

        self.faces = bg.faces

    def _permute_face_angles(self, g, face, indent):

        print ' ' * indent, 'Permute angles:'

        # Warning! These edges aren't guaranteed to be contiguous.
        poss_angles = []
        common_edges = g.get_common_edges(face)
        for node in face.nodes:
            state_idx = len(filter(lambda edge: node in edge, common_edges))
            state = NodeState(state_idx)
            if state == NodeState.known:
                poss_angles.append([g.get_explementary_angle(node)])
            elif state == NodeState.unknown:
                poss_angles.append(g.get_possible_angles(node))
            elif state == NodeState.free:
                poss_angles.append(list(Angle))
            print ' ' * (indent + 2), node, state, poss_angles[-1], nx.get_node_attributes(g, ANGLE).get(node)
        all_angle_perms = set(it.product(*poss_angles))
        return filter(lambda x: sum(x) == 360, all_angle_perms)

    def permute_layouts(self, g, face, indent):

        angle_perms = self._permute_face_angles(g, face, indent + 2)

        offset = Vector2(0, 0)
        start_dir = Direction.up
        common_edges = g.get_common_edges(face)
        if common_edges:
            edge = common_edges[0]
            rev_dir = g.edges[edge][DIRECTION]
            start_dir = Direction.opposite(rev_dir)
            offset = g.nodes[edge[1]][POSITION]

        # Turn each set of
        lengths = [g.edges.get(edge, {}).get(LENGTH) for edge in face]
        ofaces = []
        for angles in angle_perms:


            oface = OrthogonalFace(face.edges, angles, lengths[:], start_dir, offset)
            ofaces.append(oface)

            for dir_, opp_dir in (Direction.xs(), Direction.ys()):

                # Define two sides - one with the shorter proposed length and
                # one with the longer proposed length.
                min_side, max_side = oface.sides[opp_dir], oface.sides[dir_]
                if max_side.proposed_length < min_side.proposed_length:
                    min_side, max_side = max_side, min_side

                # print ' ' * (indent + 6), 'Axis:', dir_, opp_dir

                # If one of the sides has a known length then we must use that
                # length
                max_length = max_side.proposed_length
                if min_side.state == SideState.known:
                    max_length = min_side.length
                elif max_side.state == SideState.known:
                    max_length = max_side.length
                # print ' ' * (indent + 8), 'max_length:', max_length

                # If the min side is unknown, split the remainder and divide it
                # amongst the edges.
                if min_side.state == SideState.unknown:
                    min_side_edge = (max_length - min_side.known_length) / float(min_side.num_unknown_edges)
                    for edge_idx in min_side.indices:
                        oface.lengths[edge_idx] = oface.lengths[edge_idx] or min_side_edge

                # If the max side is unknown, split the remainder and divide it
                # amongst the edges.
                if max_side.state == SideState.unknown:
                    max_side_edge = (max_length - max_side.known_length) / float(max_side.num_unknown_edges)
                    for edge_idx in max_side.indices:
                        oface.lengths[edge_idx] = oface.lengths[edge_idx] or max_side_edge

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
                self.layouts.append(g_copy)


    def run(self):
        print 'Running:', self
        self._process_face(0, OrthogonalGraph(), 0)