import networkx as nx

from componentbase import ComponentBase
from ..layouters.treelayouter import TreeLayouter


class TreeComponent(ComponentBase):

    @property
    def articulation_points(self):
        nodes = set()
        for node in set(nx.articulation_points(self.p_graph)) & set(self.nodes()):
            neighbors = set(self.p_graph.neighbors(node))
            neighbors.add(node)
            if not set(self.nodes()).issuperset(neighbors):
                nodes.add(node)
        return nodes

    def layout(self):
        self.layouter = TreeLayouter(self)
        self.layouter.run()
        # try:
        #     map_gen.run()
        # except Exception, e:
        #     pos = nx.get_node_attributes(map_gen.g, POSITION)
        #     nx.draw_networkx(map_gen.g, pos)
        #     plt.show()
        #     raise