import networkx as nx

from reactor.blocks.blockbase import BlockBase
from reactor.const import POSITION
from reactor.geometry.vector import Vector2


class RootNodeBlock(BlockBase):

    @property
    def node(self):
        return list(self.data)[0]

    def get_permutations(self):
        g = nx.DiGraph()
        g.add_node(self.node, **{POSITION: Vector2(0, 0)})
        return [g]