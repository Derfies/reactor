import networkx as nx
import matplotlib.pyplot as plt

from embeddedbiconngraph import EmbeddedBiconnGraph
from orthogonallayouter import OrthogonalLayouter


class MapGenerator(object):

    def __init__(self, grid_path):
        self.g = nx.Graph(nx.read_graphml(grid_path))

        self.biconns = []
        self.layouters = []

    @property
    def biconnected_components(self):
        biconns = list(nx.biconnected_components(self.g))
        return filter(lambda s: len(s) > 2, biconns)

    @property
    def biconnected_graphs(self):
        biconn_graphs = []
        for biconn in self.biconnected_components:
            biconn_graphs.append(self.g.subgraph(biconn))
        return biconn_graphs

    def run(self):
        for biconn_graph in self.biconnected_graphs:

            # Try to run the planar layout on the bicon component. If this fails
            # show the layout for debug.
            bg = EmbeddedBiconnGraph(biconn_graph)
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