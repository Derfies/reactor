from reactor.blocks.blockbase import BlockBase
from reactor.embeddedbiconngraph import EmbeddedBiconnGraph


class CyclicBlock(BlockBase):

    def __init__(self, *args, **kwargs):
        super(CyclicBlock, self).__init__(*args, **kwargs)

        self._bg = self._calculate_faces()

    @property
    def bg(self):
        return self._bg

    def _calculate_faces(self):

        # Try to run the planar layout on the bicon component. If this fails
        # show the layout for debug.
        bg = EmbeddedBiconnGraph(self.g)
        try:
            bg.run()
        except nx.exception.NetworkXException:
            import networkx as nx
            import matplotlib.pyplot as plt

            nx.draw_networkx(bg.g, bg.pos)
            plt.show()
            raise

        return bg