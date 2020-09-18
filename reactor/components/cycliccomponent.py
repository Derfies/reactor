import networkx as nx

from componentbase import ComponentBase
from ..layouters.cycliclayouter import CyclicLayouter


class CyclicComponent(ComponentBase):

    layouter_cls = CyclicLayouter

    @property
    def articulation_points(self):
        return set(nx.articulation_points(self.g._graph)) & set(self.g.nodes())