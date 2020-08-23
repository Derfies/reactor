import networkx as nx

from const import ANGLE, DIRECTION, POSITION, LENGTH, Angle


class OrthogonalGraph(nx.Graph):

    def add_face(self, face):

        # Assert that the nodes the given face is going to connect to have a
        # maximum of 3 angles (faces) already connected.
        for node in face.nodes:
            num_faces = len(self.nodes.get(node, {}).get(ANGLE, {}))
            msg = 'Node {} has {} faces'.format(node, num_faces)
            assert num_faces < 4, msg

        # Merge edges into the graph.
        self.add_edges_from(face)

        # Merge node data into the graph.
        for node_idx, node in enumerate(face.nodes):
            attr = {face: face.angles[node_idx]}
            self.nodes[node].setdefault(ANGLE, {}).update(attr)
            self.nodes[node][POSITION] = face.positions[node_idx]

        # Merge edge data into the graph.
        for edge_idx, edge in enumerate(face):
            self.edges[edge][LENGTH] = face.lengths[edge_idx]
            self.edges[edge][DIRECTION] = face.directions[edge_idx]

    def get_existing_angles(self, node):
        return nx.get_node_attributes(self, ANGLE).get(node)

    def get_common_edges(self, face):
        return filter(lambda x: x in self.edges, face.reversed())

    def get_possible_angles(self, node):
        existing_angles = self.get_existing_angles(node)
        if existing_angles is None:
            return list(Angle)
        total = sum(existing_angles.values())
        return filter(lambda a: a <= total, Angle)

    # Rename to "get_outer_angle"?
    def get_explementary_angle(self, node):
        existing_angles = self.get_existing_angles(node)
        total = sum(map(lambda a: 180 - a, existing_angles.values()))
        return Angle(180 - (360 - total))