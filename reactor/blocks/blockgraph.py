import networkx as nx

from reactor.blocks.cyclicblock import CyclicBlock
from reactor.blocks.nodeblock import NodeBlock
from reactor.blocks.rootcyclicblock import RootCyclicBlock
from reactor.blocks.rootnodeblock import RootNodeBlock
from reactor.embeddedbiconngraph import EmbeddedBiconnGraph


class BlockGraph(object):

    def __init__(self, g):
        self._g = g
        self._biconns = ()
        self._dg = nx.DiGraph()
        self._q = nx.OrderedDiGraph()   # Adj order is important!

    @property
    def g(self):
        return self._g

    @property
    def biconns(self):
        return self._biconns

    @property
    def dg(self):
        return self._dg

    @property
    def q(self):
        return self._q

    @property
    def root(self):
        return filter(lambda n: not self.q.in_edges(n), self.q)[0]

    def get_block_class(self, block):
        return self.q.nodes[block].get('cls')

    def _calculate_oriented_graph(self):

        # Use a node from the largest biconnected component as the source. This
        # will hopefully process a larger chunk of faces / permutations first.
        biconns = sorted(self.biconns, key=lambda b: -len(b))
        print 'sorted biconns:', biconns
        source = list(biconns[0])[0]

        print 'using source:', source

        # BROKEN - this source isn't working!!!

        # TODO: Do we still need to do this anymore?
        # Yes? because dfs on the resulting quotient graph is going to be hard
        # Yes? Because each block still needs to know it's parent
        # dg = self.g.to_directed()
        # edge_dfs = list(nx.edge_dfs(self.g, source))#, 'N5')) # HAXXOR
        # del_edges = filter(lambda e: e not in edge_dfs, dg.edges())
        # dg.remove_edges_from(del_edges)

        # TODO: Bow graphs do not work. They share a node but they're ending up
        # in two different frozen sets.
        # NO
        dg = nx.dfs_tree(self.g)

        return dg

    def _calculate_quotient_graph(self):
        def partition_fn(a, b):
            return any([
                a in biconn and b in biconn and len(biconn) > 2
                for biconn in self.biconns
            ])
        return nx.quotient_graph(self.dg, partition_fn,
                                 create_using=nx.OrderedDiGraph)

    def run(self):
        self._biconns = tuple(nx.biconnected_components(self.g))
        self._dg = self._calculate_oriented_graph()
        self._q = self._calculate_quotient_graph()

        for nodes in list(self.q):
            p_nodes = next(self.q.predecessors(nodes), None)
            cls = RootNodeBlock if p_nodes is None else NodeBlock
            self.q.nodes[nodes]['cls'] = cls
            if nodes not in self.biconns:
                nx.relabel_nodes(self.q, {nodes: list(nodes)[0]}, copy=False)
            else:

                # Get the root node. If there is no parent then pick the first
                # node in the bunch, otherwise use the node connected to the
                # previous block.
                root_node = list(nodes)[0]
                if p_nodes is not None:
                    in_edge = next(nx.edge_boundary(self.g, p_nodes, nodes))
                    root_node = in_edge[1]

                # Run the cyclic component face resolver, then add the resulting
                # face graph to the quotient graph.
                bg = EmbeddedBiconnGraph(self.g.subgraph(nodes))
                bg.run()
                fg = bg.get_face_graph(root_node)
                nx.set_node_attributes(fg, CyclicBlock, 'cls')
                self.q.update(fg)

                # Add the edge from the parent to the first node of the first
                # face.
                edges = list(self.q.edges(nodes))
                self.q.remove_edges_from(edges)
                root_face = filter(lambda n: not fg.in_edges(n), fg)[0]
                self.q.nodes[root_face]['cls'] = RootCyclicBlock
                edges.insert(0, (nodes, root_face))
                self.q.add_edges_from(edges)
                nx.relabel_nodes(self.q, {nodes: root_node}, copy=False)
