import networkx as nx
import matplotlib.pyplot as plt

from embeddedbiconngraph import EmbeddedBiconnGraph
from orthogonallayouter import OrthogonalLayouter
from tree_layout import MapGenerator as TreeLayouter
from const import POSITION


class MapGenerator(object):

    def __init__(self, grid_path):
        self.g = nx.Graph(nx.read_graphml(grid_path))

        self.biconns = []
        self.layouters = []
        self.trees = []

        # Make sure each node is max incident of 4.
        for node in self.g.nodes():
            node_edges = self.g.edges(node)
            assert len(node_edges) < 5, 'Node: {} has incident value greater than 4'.format(node)

    @property
    def cyclic_components(self):
        biconns = list(nx.biconnected_component_subgraphs(self.g))
        return filter(lambda s: len(s) > 2, biconns)

    @property
    def tree_components(self):
        g = self.g.copy()
        for comp in self.cyclic_components:
            g.remove_nodes_from(comp)
        return nx.connected_component_subgraphs(g)

    def run(self):
        for cyclic_component in self.cyclic_components:

            # Try to run the planar layout on the bicon component. If this fails
            # show the layout for debug.
            bg = EmbeddedBiconnGraph(cyclic_component)
            self.biconns.append(bg)
            try:
                bg.run()
            except nx.exception.NetworkXException:
                nx.draw_networkx(bg.g, bg.pos)
                plt.show()
                raise

            ol = OrthogonalLayouter(bg.faces)
            ol.run()

            self.layouters.append(ol)

        for tree_component in self.tree_components:
            map_gen = TreeLayouter(tree_component)
            self.trees.append(map_gen)
            try:
                map_gen.run()
            except Exception, e:
                pos = nx.get_node_attributes(map_gen.g, POSITION)
                nx.draw_networkx(map_gen.g, pos)
                plt.show()
                raise