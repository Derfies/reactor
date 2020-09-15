import networkx as nx

from componentbase import ComponentBase
from ..embeddedbiconngraph import EmbeddedBiconnGraph
from ..layouters.cycliclayouter import CyclicLayouter


class CyclicComponent(ComponentBase):

    @property
    def articulation_points(self):
        return set(nx.articulation_points(self.p_graph)) & set(self.nodes())

    def layout(self):

        # Try to run the planar layout on the bicon component. If this fails
        # show the layout for debug.
        bg = EmbeddedBiconnGraph(self)
        try:
            bg.run()
        except nx.exception.NetworkXException:
            nx.draw_networkx(bg.g, bg.pos)
            plt.show()
            raise

        self.layouter = CyclicLayouter(bg.faces)
        self.layouter.run()