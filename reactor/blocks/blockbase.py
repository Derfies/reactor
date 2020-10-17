import abc

import networkx as nx


class BlockBase(nx.DiGraph):

    __metaclass__ = abc.ABCMeta

    def __str__(self):
        return str(self.edges)

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
