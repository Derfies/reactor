import itertools as it

import networkx as nx

from reactor.blocks.edgeblock import EdgeBlock
from reactor.blocks.faceblock import FaceBlock
from reactor.blocks.rootblock import RootBlock
from reactor.faceanalysis import FaceAnalysis
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


class BlockGraphCreator(object):

    """
    TODO: Merge with primary layouter class.
    """

    def __init__(self, g):
        self._g = g

    @property
    def g(self):
        return self._g

    def _sort_nodes(self, nodes):
        """
        Sort criteria:
        - Prioritise faces
        - Priortise smaller faces
        - Sorted tuple

        """
        return sorted(nodes, key=lambda n: (len(n) < 3, len(n), sorted(n)))

    def bfs_tree(self, g, source, reverse=False, depth_limit=None, sort_neighbors=None):
        t = BlockGraph()
        t.add_node(source)
        edges_gen = nx.bfs_edges(
            g,
            source,
            reverse=reverse,
            depth_limit=depth_limit,
            sort_neighbors=sort_neighbors,
        )
        t.add_edges_from(edges_gen)
        return t

    # TODO: Make this class the actual quotient graph and make this a class
    # method.
    def get_block_graph(self):

        # Split the input graph into biconnected components. Each biconn will
        # become a node in the block graph.
        g = nx.Graph()

        # Build nodes.
        for biconn in nx.biconnected_components(self.g):
            sg = self.g.subgraph(biconn)
            if len(biconn) < 3:
                g.add_node(EdgeBlock(sg))
            else:
                faces = FaceAnalysis(sg).get_faces()
                g.add_nodes_from(map(FaceBlock.from_path, faces))

        # Build edges.
        edges = filter(lambda x: x[0].is_adjacent(x[1]), it.combinations(g, 2))
        g.add_edges_from(edges)

        # Find root node.
        sorted_nodes = self._sort_nodes(g)
        root = sorted_nodes[0]

        # Put a super root behind the root node. This will place the very first
        # node at the origin.
        super_root = RootBlock(self.g.subgraph([sorted(root)[0]]))
        g.add_edge(super_root, root)

        # Orient graph. Sort neighbours so that faces are visited first from
        # smallest to largest, then other biconns.
        g = self.bfs_tree(g, super_root, sort_neighbors=self._sort_nodes)

        # Sort nodes.
        for node in g:
            p_node = g.parent(node)
            node.sort(p_node)

        return g