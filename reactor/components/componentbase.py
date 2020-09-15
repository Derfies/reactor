import abc

import networkx as nx


class ComponentBase(nx.Graph):

    __metaclass__ = abc.ABCMeta

    def __init__(self, p_graph, g):
        super(ComponentBase, self).__init__()
        self.add_edges_from(g.edges())

        self.p_graph = p_graph
        self.layouter = None

    @abc.abstractproperty
    def articulation_points(self):
        """"""

    @abc.abstractmethod
    def layout(self):
        """"""