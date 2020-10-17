import math

import networkx as nx

from reactor.const import POSITION


class FaceAnalysis(object):

    def __init__(self, g, do_layout=False):
        self._do_layout = do_layout
        self._visited = set()

        self._g = g
        self._pos = {}
        self._embedding = nx.PlanarEmbedding()
        self._ext_hedge = None
        self._ext_face = None
        self._faces = tuple()

    @property
    def g(self):
        return self._g

    @property
    def pos(self):
        return self._pos

    @property
    def embedding(self):
        return self._embedding

    @property
    def ext_hedge(self):
        return self._ext_hedge

    @property
    def ext_face(self):
        return self._ext_face

    @property
    def faces(self):
        return self._faces

    def _calculate_node_positions(self):
        """
        Return a dictionary containing the positions of all nodes in the graph.
        If the graph was read from file it may include positional data for all
        nodes. If do_layout is False read this data from file otherwise perform
        a planar layout. This may not give results as expected, so watch out!

        """
        if self._do_layout:
            return nx.get_node_attributes(self.g, POSITION)
        else:
            return nx.planar_layout(self.g)

    def _calculate_planar_embedding(self):
        """
        Return a planar embedding for the graph, using the planar layout
        calculated previously. If the previous layout step has not resulted in a
        planar layout then the embedding will fail.

        """
        emd = nx.PlanarEmbedding()
        for node in self.g:
            neigh_pos = {
                neigh: (
                    self.pos[neigh][0] - self.pos[node][0],
                    self.pos[neigh][1] - self.pos[node][1]
                ) for neigh in self.g[node]
            }
            neighs_sorted = sorted(
                self.g.adj[node],
                key=lambda v: math.atan2(neigh_pos[v][1], neigh_pos[v][0])
            )  # counter clockwise
            last = None
            for neigh in neighs_sorted:
                emd.add_half_edge_ccw(node, neigh, last)
                last = neigh
        emd.check_structure()
        return emd

    def _calculate_external_face_half_edge(self):
        """
        Return a half-edge on the external face. We do this by selecting a node
        in the bottom left corner, then an adjacent node with the maximal cosine
        value.

        """
        corner = min(self.pos, key=lambda n: tuple(self.pos[n]))
        other = max(
            self.g.adj[corner], key=lambda node:
            (self.pos[node][1] - self.pos[corner][1]) /
            math.hypot(
                self.pos[node][0] - self.pos[corner][0],
                self.pos[node][1] - self.pos[corner][1]
            )
        )  # maximum cosine value
        return other, corner

    def _get_edge_face(self, edge):
        """

        """
        return tuple(self.embedding.traverse_face(
            *edge,
            mark_half_edges=self._visited
        ))

    def _calculate_exterior_face(self):
        """

        """
        return self._get_edge_face(self.ext_hedge)

    def _calculate_interior_faces(self):
        """
        Return all faces for the graph using the planar embedding, exclusing the
        exterior face. This should return all faces with their nodes in the same
        rotation-wise order.

        """
        return [
            self._get_edge_face(edge)
            for edge in self.embedding.edges
            if edge not in self._visited
        ]

    def run(self):
        self._pos = self._calculate_node_positions()
        self._embedding = self._calculate_planar_embedding()
        self._ext_hedge = self._calculate_external_face_half_edge()
        self._ext_face = self._calculate_exterior_face()
        self._faces = self._calculate_interior_faces()