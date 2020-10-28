import networkx as nx


from reactor.layouters.edgelayouter import EdgeLayouter
from reactor.layouters.facelayouter import FaceLayouter
from reactor.layouters.rootfacelayouter import RootFaceLayouter
from reactor.layouters.rootlayouter import RootLayouter


LAYOUTER = 'layouter'


class BlockGraph(nx.DiGraph):

    def parent(self, node):
        return next(self.predecessors(node), None)

    def get_layouter(self, node):
        if self.nodes[node].get(LAYOUTER) is None:
            if len(node) > 2:
                if len(self.parent(node)) > 2:
                    cls = FaceLayouter
                else:
                    cls = RootFaceLayouter
            elif len(node) > 1:
                cls = EdgeLayouter
            else:
                cls = RootLayouter
            self.nodes[node][LAYOUTER] = cls(node, self)
        return self.nodes[node][LAYOUTER]
