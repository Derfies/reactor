import networkx as nx

from componentbase import ComponentBase
from ..layouters.treelayouter import TreeLayouter


class TreeComponent(ComponentBase):

    layouter_cls = TreeLayouter

    @property
    def articulation_points(self):

        # FIX ME
        # Doesn't work because parent graph != subgraph's graph.
        nodes = set()
        for node in set(nx.articulation_points(self.g._graph)) & set(self.g.nodes()):
            neighbors = set(self.g._graph.neighbors(node))
            neighbors.add(node)
            if not set(self.g.nodes()).issuperset(neighbors):
                nodes.add(node)
        return nodes