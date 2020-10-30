import itertools as it

import networkx as nx

from reactor.blocks.edgeblock import EdgeBlock
from reactor.blocks.faceblock import FaceBlock
from reactor.blocks.rootblock import RootBlock
from reactor.const import POSITION
from reactor.faceanalysis import FaceAnalysis
from reactor.layouters.edgelayouter import EdgeLayouter
from reactor.layouters.facelayouter import FaceLayouter
from reactor.layouters.rootfacelayouter import RootFaceLayouter
from reactor.layouters.rootlayouter import RootLayouter


class Layouter(object):

    def __init__(self, g, map_):
        self._g = g
        self._map = map_

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

    def get_layouter_class(self, g, node):
        if len(node) > 2:
            parent = next(g.predecessors(node))
            if len(parent) > 2:
                return FaceLayouter
            else:
                return RootFaceLayouter
        elif len(node) > 1:
            return EdgeLayouter
        else:
            return RootLayouter

    def bfs_tree(self, g, source, sort_neighbors):
        g1 = nx.bfs_tree(g, source, sort_neighbors=sort_neighbors)
        layouters = {
            node: self.get_layouter_class(g1, node)(node, self._map.layout)
            for node in g1
        }
        t = nx.DiGraph()
        for head, tail in g1.edges:
            t.add_edge(layouters[head], layouters[tail])
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
                for face in FaceAnalysis(sg).get_faces():
                    fsg = self.g.subgraph(face)
                    g.add_node(FaceBlock.from_path(face, fsg))

        # Build edges.
        edges = filter(lambda x: x[0].is_adjacent(x[1]), it.combinations(g, 2))
        g.add_edges_from(edges)

        # Find the root node and put a super root behind it. This will place the
        # very first node at the origin.
        sorted_nodes = self._sort_nodes(g)
        root = sorted_nodes[0]
        super_root = RootBlock(self.g.subgraph([sorted(root)[0]]))
        g.add_edge(super_root, root)

        # Orient graph. Sort neighbours so that faces are visited first from
        # smallest to largest, then other biconns.
        g = self.bfs_tree(g, super_root, self._sort_nodes)

        # Sort nodes.
        # TODO: Can possibly merge with function above?
        for node in g:
            parent = next(g.predecessors(node), None)
            if parent is not None:
                parent = parent.data
            node.data.sort(parent)

        return g

    def layout_graph(self, g):

        i = 0
        layouters = list(g)
        while i < len(layouters):

            if layouters[i].done:
                i += 1
                continue

            print('PROCESS:', i, list(layouters[i].data.edges))

            # Problem is here. If a child fails and we go back to parent, we
            # just regenerate the permutations again, which we already know
            # failed.
            # Dont always regenerate.
            # Only generate when we hit this guy for the first time, not when
            # we've returned here after a child failed.
            layouters[i].init_permutations()
            print('    NUM PERMS:', len(layouters[i].permutations))

            while layouters[i].permutations:
                perm = layouters[i].permutations.pop()
                if not layouters[i].can_lay_out(perm):
                    print('    FAILED:', nx.get_node_attributes(perm, POSITION))
                    continue
                layouters[i].add_to_layout(perm)
                print('    SUCCESS:', nx.get_node_attributes(perm, POSITION))
                i += 1
                break
            else:

                # Move the cursor back to the parent.
                parent = next(g.predecessors(layouters[i]))
                while layouters[i] != parent:
                    i -= 1

                print('    REMOVING FROM:', list(layouters[i].data.edges))

                # Mark all layouters under the parent as not done and remove
                # their permutations.
                # Remove the failed layouters from the layout.
                for layouter in nx.dfs_tree(g, layouters[i]):
                    if layouter.done:
                        print('    REMOVING:', list(layouter.data.edges))
                        layouter.remove_from_layout()
                        if layouter != layouters[i]:
                            print('    CLEARING:', list(layouter.data.edges))
                            layouter.permutations.clear()

    def run(self):
        self.layout_graph(self.get_block_graph())
        print('complete:', len(self.g) == len(self._map.layout))
        print('remainging:', set(self.g) - set(self._map.layout))
