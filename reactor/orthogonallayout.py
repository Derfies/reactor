import networkx as nx

from reactor.const import ANGLE, Angle


class OrthogonalLayout(nx.DiGraph):

    def get_existing_angles(self, node):
        return nx.get_node_attributes(self, ANGLE).get(node)

    def get_common_edges(self, face):
        return filter(lambda x: x in self.edges, face.edges_reverse())

    def get_possible_angles(self, node):
        existing_angles = self.get_existing_angles(node)
        if existing_angles is None:
            return list(Angle)
        total = sum(existing_angles.values())
        return tuple(filter(lambda a: a <= total, Angle))

    # Rename to "get_outer_angle"?
    def get_explementary_angle(self, node):
        existing_angles = self.get_existing_angles(node)
        total = sum(map(lambda a: 180 - a, existing_angles.values()))
        return Angle(180 - (360 - total))