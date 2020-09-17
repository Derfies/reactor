import random

import networkx as nx
import matplotlib.pyplot as plt

from const import POSITION
from components.treecomponent import TreeComponent
from components.cycliccomponent import CyclicComponent
from vector import Vector2


class Final(nx.Graph):

    def get_component_offset(self, comp):
        offsets = []
        for node in set(comp) & set(self):
            self_pos = self.nodes[node][POSITION]
            other_pos = comp.nodes[node][POSITION]
            offset = self_pos - other_pos
            offsets.append(offset)

        offsets_same = all(offsets[0] == other for other in offsets[1:])
        assert offsets_same, 'All nodes of input component must have same offset'

        offset = Vector2(0, 0)
        if offsets:
            offset = offsets[0]
        return offset

    def add_component(self, comp):

        # TODO: Create new base graph class using parts of OrthogonalGraph.

        # Calculate offset.
        offset = self.get_component_offset(comp)

        # Merge edges into the graph.
        self.add_edges_from(comp.edges())
        print 'added:', list(comp)
        print 'nodes now:', list(self.nodes())
        print 'edges now:', list(self.edges())

        # Merge node data into the graph.
        pos = nx.get_node_attributes(comp, POSITION)
        for node in comp:
            print '   adding postition for:', node
            self.nodes[node][POSITION] = pos[node] + offset


class MapGenerator(object):

    def __init__(self, grid_path):
        self.g = nx.Graph(nx.read_graphml(grid_path))

        # Make sure each node is max incident of 4.
        for node in self.g.nodes():
            node_edges = self.g.edges(node)
            assert len(node_edges) < 5, 'Node: {} has incident value greater than 4'.format(node)

    @property
    def cyclic_components(self):
        sgs = list(nx.biconnected_component_subgraphs(self.g))

        # Ignore dyads (I think that's what they're called). Which are just
        # single floating edges.
        sgs = filter(lambda s: len(s) > 2, sgs)
        return [CyclicComponent(self.g, sg) for sg in sgs]

    @property
    def tree_components(self):
        sgs = list(nx.biconnected_component_subgraphs(self.g))
        sgs = filter(lambda s: len(s) < 3, sgs)
        g = nx.Graph()
        g.add_edges_from(sgs)
        return [
            TreeComponent(self.g, sg)
            for sg in nx.connected_component_subgraphs(g)
        ]

    def run(self):

        # Munge all components into a single, randomised list. If there are any
        # cyclic components, put a random one at the start of the list.
        cyclic_comps = self.cyclic_components
        comps = cyclic_comps + self.tree_components
        random.shuffle(comps)
        if cyclic_comps:
            cyclic_comp = random.choice(cyclic_comps)
            comps.remove(cyclic_comp)
            comps.insert(0, cyclic_comp)

        # Build articulation point / component dictionary.
        connections = {}
        for comp in comps:
            for point in comp.articulation_points:
                connections.setdefault(point, []).append(comp)

        # Stitch components together.
        final = Final()
        while comps:
            comp = comps.pop(0)
            comp.layout()

            layout = comp.layouter.layouts[0] # TODO: Take random
            final.add_component(layout)

            pos = nx.get_node_attributes(comp.layouter.layouts[0], POSITION)
            nx.draw_networkx(comp.layouter.layouts[0], pos)
            plt.show()


        pos = nx.get_node_attributes(final, POSITION)
        nx.draw_networkx(final, pos)
        plt.show()