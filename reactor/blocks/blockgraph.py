import networkx as nx
from networkx.algorithms.minors import _quotient_graph
from networkx.utils import arbitrary_element

from reactor.blocks.cyclicblock import CyclicBlock
from reactor.blocks.nodeblock import NodeBlock
from reactor.blocks.rootcyclicblock import RootCyclicBlock
from reactor.blocks.rootnodeblock import RootNodeBlock
from reactor.embeddedbiconngraph import EmbeddedBiconnGraph


def equivalence_classes(iterable, relation):
    """Returns the set of equivalence classes of the given `iterable` under
    the specified equivalence relation.

    `relation` must be a Boolean-valued function that takes two argument. It
    must represent an equivalence relation (that is, the relation induced by
    the function must be reflexive, symmetric, and transitive).

    The return value is a set of sets. It is a partition of the elements of
    `iterable`; duplicate elements will be ignored so it makes the most sense
    for `iterable` to be a :class:`set`.

    """
    # For simplicity of implementation, we initialize the return value as a
    # list of lists, then convert it to a set of sets at the end of the
    # function.
    blocks = []
    # Determine the equivalence class for each element of the iterable.
    for y in iterable:
        # Each element y must be in *exactly one* equivalence class.
        #
        # Each block is guaranteed to be non-empty
        for block in blocks:
            x = arbitrary_element(block)
            if relation(x, y):
                block.append(y)
                break
        else:
            # If the element y is not part of any known equivalence class, it
            # must be in its own, so we create a new singleton equivalence
            # class for it.
            blocks.append([y])

    # HAXXOR
    seen = set()
    seen_add = seen.add
    frozen_sets = []
    for block in blocks:
        frozen_set = frozenset(block)
        if not (frozen_set in seen or seen_add(frozen_set)):
            frozen_sets.append(frozen_set)
    return frozen_sets


class BlockGraph(object):

    def __init__(self, g):
        self._g = g
        self._biconns = ()
        self._dg = nx.DiGraph()
        self._q = nx.DiGraph()   # Adj order is important!

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
        return next(filter(lambda n: not self.q.in_edges(n), self.q))#[0]

    def get_block_class(self, block):
        return self.q.nodes[block].get('cls')

    def _calculate_oriented_graph(self):

        # Use a node from the largest biconnected component as the source. This
        # will hopefully process a larger chunk of faces / permutations first.
        biconns = sorted(self.biconns, key=lambda b: (len(b), b), reverse=True)

        source = None
        if biconns:
            source = sorted(biconns[0])[0]

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
        dg = nx.dfs_tree(self.g, source)

        return dg

    def _calculate_quotient_graph(self):
        def partition_fn(a, b):
            return any([
                a in biconn and b in biconn and len(biconn) > 2
                for biconn in self.biconns
            ])
        partition = equivalence_classes(self.dg, partition_fn)
        return _quotient_graph(self.dg, partition)

    def run(self):
        self._biconns = tuple(nx.biconnected_components(self.g))
        self._dg = self._calculate_oriented_graph()
        dfs_nodes = list(nx.dfs_preorder_nodes(self.dg))
        self._q = self._calculate_quotient_graph()

        for nodes in list(nx.dfs_preorder_nodes(self.q, self.root)):
            p_nodes = next(self.q.predecessors(nodes), None)
            cls = RootNodeBlock if p_nodes is None else NodeBlock
            self.q.nodes[nodes]['cls'] = cls
            if nodes not in self.biconns:
                nx.relabel_nodes(self.q, {nodes: list(nodes)[0]}, copy=False)
            else:

                # Get the root node. If there is no parent then pick the first
                # node in the bunch, otherwise use the node connected to the
                # previous block.
                sorted_nodes = sorted(nodes, key=lambda n: dfs_nodes.index(n))
                root_node = sorted_nodes[0]
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
                root_face = next(filter(lambda n: not fg.in_edges(n), fg))#[0]
                self.q.nodes[root_face]['cls'] = RootCyclicBlock
                edges.insert(0, (nodes, root_face))
                self.q.add_edges_from(edges)
                nx.relabel_nodes(self.q, {nodes: root_node}, copy=False)