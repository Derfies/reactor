import networkx as nx

from reactor import utils
from reactor.blocks.nodeblock import NodeBlock
from reactor.blocks.cyclicblock import CyclicBlock
from reactor.const import POSITION


class OrthogonalLayouter(object):

    def __init__(self, g):
        self._g = g
        self._dg = nx.DiGraph()
        self._q = nx.DiGraph()
        self._layout = nx.DiGraph()

    @property
    def g(self):
        return self._g

    @property
    def dg(self):
        return self._dg

    @property
    def q(self):
        return self._q

    @property
    def layout(self):
        return self._layout

    @property
    def root_node(self):
        return filter(lambda x: not self.q.in_edges(x), self.q.nodes())[0]

    def _calculate_oriented_edge_graph(self):
        dg = self.g.to_directed()
        dfs_edges = list(nx.edge_dfs(self.g))
        del_edges = filter(lambda e: e not in dfs_edges, dg.edges())
        dg.remove_edges_from(del_edges)
        return dg

    def _calculate_quotient_graph(self):
        biconns = list(nx.biconnected_components(self.g))

        def partition_fn(a, b):
            return any([
                a in biconn and b in biconn and len(biconn) > 2
                for biconn in biconns
            ])

        return nx.quotient_graph(self.dg, partition_fn)

    def get_block_class(self, nodes):
        return CyclicBlock if len(nodes) > 1 else NodeBlock

    def _process_block(self, block):
        print 'process:', list(block.g.nodes()), 'parent:', block.parent_block_node

        result = False
        for perm in block.get_permutations():

            # Test to see if the block can be laid out. If so, merge into main
            # layout.
            if not block.can_lay_out(perm):
                print '    **** FAILED:', nx.get_node_attributes(perm, POSITION)
                continue
            self.layout.update(perm)

            # Recurse children.
            child_results = []
            for child in self.q.successors(block):

                # If a child failed to be placed, remove the entire subgraph.
                child_result = self._process_block(child)
                child_results.append(child_result)
                if not child_result:
                    del_nodes = nx.dfs_tree(self.layout, block.root_node)
                    print '**** REMOVE SUBGRAPH:', list(del_nodes)
                    self.layout.remove_nodes_from(del_nodes)
                    #result = False
                    break

            # All children be laid out, so we can stop looping this block's
            # permutations.
            result = all(child_results)
            if result:
                break

        else:
            print '#### TOTALLY FAILED:'.format(block)#, result
            #result = False

        # pos = nx.get_node_attributes(self.layout, POSITION)
        # utils.draw(self.layout, pos)

        return result

    def run(self):

        # Calculate edges oriented to dfs.
        self._dg = self._calculate_oriented_edge_graph()

        # Replace nodes in the tree with block classes.
        q = self._calculate_quotient_graph()
        mapping = {}
        for nodes in q.nodes():
            block_cls = self.get_block_class(nodes)
            sg = self.dg.subgraph(nodes)
            mapping[nodes] = block_cls(sg, q, self.layout)
        self._q = nx.relabel_nodes(q, mapping, copy=False)

        self._process_block(self.root_node)