import networkx as nx

from orthogonallayouter import OrthogonalLayouter


class MapGenerator(object):

    def __init__(self, grid_path):
        self.g = nx.read_graphml(grid_path).to_undirected()

        # Make sure each node has max incident of 4.
        for node in self.g.nodes():
            node_edges = self.g.edges(node)
            assert len(node_edges) < 5, 'Node: {} has incident value greater than 4'.format(node)

    def run(self):
        layouter = OrthogonalLayouter(self.g)
        layouter.run()


        from reactor import utils
        from reactor.const import POSITION

        print 'complete:', len(self.g) == len(layouter.layout)
        pos = nx.get_node_attributes(layouter.layout, POSITION)
        utils.draw(layouter.layout, pos)