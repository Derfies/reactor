import abc

import networkx as nx


class BlockBase(nx.DiGraph):

    __metaclass__ = abc.ABCMeta

    def __init__(self, subgraph=None):
        super(BlockBase, self).__init__()

        if subgraph is not None:
            self.add_nodes_from(subgraph.nodes)
            self.add_edges_from(subgraph.edges)
            self._update_attributes(subgraph)

    def __str__(self):
        return str(self.edges)

    def _update_attributes(self, g):

        # I wish there was a better way to do this. We're trying to retain
        # data from the input subgraph, but it's a graph and the block is a
        # digraph. We need to attempt both edge directions to ensure the
        # data is passed on.
        nx.set_node_attributes(self, dict(g.nodes(data=True)))
        for u, v, data in g.edges(data=True):
            nx.set_edge_attributes(self, {(u, v): data})
            nx.set_edge_attributes(self, {(v, u): data})

    @property
    @abc.abstractmethod
    def root(self):
        """"""

    @abc.abstractmethod
    def is_adjacent(self, other):
        """"""

    @abc.abstractmethod
    def sort(self, parent):
        """"""
