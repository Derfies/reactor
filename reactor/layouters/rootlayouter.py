import networkx as nx

from reactor.layouters.layouterbase import LayouterBase
from reactor.const import POSITION
from reactor.geometry.vector import Vector2


class RootLayouter(LayouterBase):

    def get_permutations(self):
        node = next(iter(self.data))
        g = nx.DiGraph()
        g.add_node(node, **{POSITION: Vector2(0, 0)})
        return [g]
