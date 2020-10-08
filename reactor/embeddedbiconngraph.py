import math
import itertools as it

import networkx as nx

from reactor.const import POSITION
from reactor.face import Face


class EmbeddedBiconnGraph(object):

    def __init__(self, g):
        self._g = g         # Does this have to be di/graph?

        self._pos = {}
        self._embedding = nx.PlanarEmbedding()
        self._ext_hedge = None
        self._ext_face = None

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

    def _calculate_planar_layout(self):
        """
        Return a planar layout for the graph. Note that we're trialling several
        different solutions here as some layout algorithms are not producing
        planar layouts as advertised, resulting in a borked planar embedding.

        """

        # TODO: Make this a switch
        return nx.get_node_attributes(self.g, POSITION)
        #return nx.planar_layout(self.g)

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
            neighes_sorted = sorted(
                self.g.adj[node],
                key=lambda v: math.atan2(neigh_pos[v][1], neigh_pos[v][0])
            )  # counter clockwise
            last = None
            for neigh in neighes_sorted:
                emd.add_half_edge_ccw(node, neigh, last)
                last = neigh
        try:
            emd.check_structure()
        except nx.exception.NetworkXException:
            from reactor import utils
            utils.draw_graph(self.g, self.pos)
            raise

        # from reactor import utils
        # utils.draw_graph(self.g, self.pos)

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

    def get_face_graph(self):

        def edge_relation(b, c):
            c_edges = [tuple(reversed(e)) for e in c.edges]
            return set(b.edges) & set(c_edges)

        g = nx.Graph()
        g.add_nodes_from(self._faces)
        edges = filter(lambda x: edge_relation(*x), it.combinations(g, 2))
        g.add_edges_from(edges)

        return g

    def _calculate_faces(self):
        """
        Return all faces for the graph using the planar embedding. Note that
        this includes the exterior face of the graph. This should return all
        faces with their nodes in the same rotation-wise order.
        """
        faces = []
        visited = set()
        for edge in self.embedding.edges:
            if edge in visited:
                continue
            nodes = self.embedding.traverse_face(*edge, mark_half_edges=visited)
            faces.append(Face.from_path(nodes))  # Nodes are in edge order.

        # def filter_face(face):
        #     ignore = any([self.g.edges[e].get(IGNORE) for e in face.edges])
        #     return not(ignore or self.ext_hedge in face.edges)

        return list(filter(lambda f: self.ext_hedge not in f.edges, faces))

    def run(self):
        self._pos = self._calculate_planar_layout()
        self._embedding = self._calculate_planar_embedding()
        self._ext_hedge = self._calculate_external_face_half_edge()
        ext_nodes = self.embedding.traverse_face(*self.ext_hedge)
        self._ext_face = Face.from_path(ext_nodes)

        self._faces = self._calculate_faces()

        # # Outright fail if any face is less than 4 edges. We can change this to
        # # try to insert new dummy nodes in the future.
        # assert all([
        #     len(face) >= 4
        #     for face in self.faces
        # ]), 'Cannot close polygon with less than 4 nodes'