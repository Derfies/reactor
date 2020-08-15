import math

import networkx as nx

from face import Face


class EmbeddedBiconnGraph(object):

    def __init__(self, g):
        self._g = g

        self._pos = {}
        self._embedding = nx.PlanarEmbedding()
        self._all_faces = []
        self._ext_hedge = None
        self._faces = []

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
    def all_faces(self):
        return self._all_faces

    @property
    def ext_hedge(self):
        return self._ext_hedge

    @property
    def faces(self):
        return self._faces

    def _calculate_planar_layout(self):
        #return nx.spectral_layout(self.g)
        return nx.spring_layout(self.g, seed=1)
        #return nx.nx_agraph.graphviz_layout(self.g, prog='neato')

    def _calculate_planar_embedding(self):
        """only straight line in G."""
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
        emd.check_structure()
        return emd

    def _calculate_all_faces(self):
        faces = []
        visited = set()
        for edge in self.embedding.edges():
            if edge in visited:
                continue
            nodes = self.embedding.traverse_face(*edge, mark_half_edges=visited)

            # Nodes are guaranteed to be in edge order.
            faces.append(Face.from_nodes(nodes))
        return faces

    def _calculate_external_face_half_edge(self):
        corner = min(self.pos, key=lambda n: (self.pos[n][0], self.pos[n][1]))
        other = max(
            self.g.adj[corner], key=lambda node:
            (self.pos[node][1] - self.pos[corner][1]) /
            math.hypot(
                self.pos[node][0] - self.pos[corner][0],
                self.pos[node][1] - self.pos[corner][1]
            )
        )  # maximum cosine value
        return (other, corner)

    def _calculate_inner_faces(self):
        int_faces = filter(lambda x: self.ext_hedge not in x, self.all_faces)

        # Build edge -> face dict.
        edge_to_face = {}
        for face in int_faces:
            edge_to_face.update(dict.fromkeys(face, face))

        faces = []
        smallest_face = sorted(int_faces, key=lambda n: len(n))[0]
        s = [smallest_face]
        while s:
            face = s.pop()
            if face in faces:
                continue
            faces.append(face)

            edge_to_adj_face = {}
            for rev_edge in face.reverse():
                adj_face = edge_to_face.get(rev_edge)
                if adj_face is not None and adj_face not in edge_to_adj_face:
                    edge_to_adj_face[rev_edge] = adj_face
            edge_to_adj_face = sorted(edge_to_adj_face.items(),
                                      key=lambda x: len(x[1]))

            for edge, adj_face in reversed(edge_to_adj_face):
                s.append(adj_face.set_from_edge(edge))

        return faces

    def run(self):
        self._pos = self._calculate_planar_layout()
        self._embedding = self._calculate_planar_embedding()
        self._all_faces = self._calculate_all_faces()
        self._ext_hedge = self._calculate_external_face_half_edge()
        self._faces = self._calculate_inner_faces()

        # Outright fail if any face is less than 4 edges. We can change this to
        # try to insert new dummy nodes in the future.
        assert all([
            len(face) >= 4
            for face in self.faces
        ]), 'Cannot close polygon with less than 4 nodes'