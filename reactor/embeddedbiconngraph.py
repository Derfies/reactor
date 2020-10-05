import math

import networkx as nx

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

    def get_face_graph(self, root_node):

        visited = set()
        face_graph = nx.DiGraph()

        # TODO: Remove recursive and use stack?
        def recurse_edge(edge, p_face=None):

            if edge in visited:
                return

            # Get the nodes that make up the face. Nodes are guaranteed to be in
            # edge order.
            nodes = self.embedding.traverse_face(*edge, mark_half_edges=visited)
            face = Face.from_path(nodes)
            face.set_source_edge(edge)    # Order from the input edge.

            if self.ext_hedge not in face.edges():
                face_graph.add_node(face)
                if p_face is not None:
                    face_graph.add_edge(p_face, face)
                for next_edge in face.edges_reverse():
                    recurse_edge(next_edge, face)

        edges = filter(lambda x: x not in self.ext_face.edges(), self.embedding.edges())
        edges = sorted(edges, key=lambda x: x[0] != root_node)
        recurse_edge(edges[0])

        # TODO: Reorder successors in face-complexity order.
        return face_graph

    def run(self):
        self._pos = self._calculate_planar_layout()
        self._embedding = self._calculate_planar_embedding()
        self._ext_hedge = self._calculate_external_face_half_edge()
        ext_nodes = self.embedding.traverse_face(*self.ext_hedge)
        self._ext_face = Face.from_path(ext_nodes)

        # # Outright fail if any face is less than 4 edges. We can change this to
        # # try to insert new dummy nodes in the future.
        # assert all([
        #     len(face) >= 4
        #     for face in self.faces
        # ]), 'Cannot close polygon with less than 4 nodes'