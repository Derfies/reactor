import networkx as nx

from reactor.blocks.blockbase import BlockBase
from reactor.const import POSITION
from reactor.geometry.vector import Vector2


class RootNodeBlock(BlockBase):

    def get_permutations(self):
        g = nx.DiGraph()
        g.add_node(self.data, **{POSITION: Vector2(0, 0)})
        return [g]