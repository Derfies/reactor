import random

import networkx as nx
import matplotlib.pyplot as plt

from const import POSITION, DIRECTION
from components.treecomponent import TreeComponent
from components.cycliccomponent import CyclicComponent
from vector import Vector2


class Final(nx.DiGraph):

    def get_component_offset(self, comp):
        offsets = []
        for node in set(comp) & set(self):
            self_pos = self.nodes[node][POSITION]
            other_pos = comp.nodes[node][POSITION]
            offset = self_pos - other_pos
            offsets.append(offset)

        # print 'offsets:', offsets
        # for other in offsets[1:]:
        #     print offsets[0], other
        #     print offsets[0] == other

        offsets_same = all((offsets[0] == other).all() for other in offsets[1:])
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
        # print 'added:', list(comp)
        # print 'nodes now:', list(self.nodes())
        # print 'edges now:', list(self.edges())

        # Merge node data into the graph.
        pos = nx.get_node_attributes(comp, POSITION)
        for node in comp:
            #print '   adding postition for:', node
            self.nodes[node][POSITION] = pos[node] + offset

        # Merge edge data into the graph.
        for edge in comp.edges():
            #self.edges[edge][LENGTH] = face.lengths[edge_idx]
            self.edges[edge][DIRECTION] = comp.edges[edge][DIRECTION]


class MapGenerator(object):

    def __init__(self, grid_path):
        self.g = nx.Graph(nx.read_graphml(grid_path))
        self.final = Final()

        # Make sure each node is max incident of 4.
        for node in self.g.nodes():
            node_edges = self.g.edges(node)
            assert len(node_edges) < 5, 'Node: {} has incident value greater than 4'.format(node)

    @property
    def cyclic_components(self):
        sgs = list(nx.biconnected_component_subgraphs(self.g, False))

        # Ignore dyads (I think that's what they're called). Which are just
        # single floating edges.
        sgs = filter(lambda s: len(s) > 2, sgs)
        # for sg in sgs:
        #     print sg._graph
        return [CyclicComponent(sg) for sg in sgs]

    @property
    def tree_components(self):
        sgs = list(nx.biconnected_component_subgraphs(self.g))
        sgs = filter(lambda s: len(s) < 3, sgs)
        g = nx.Graph()
        g.add_edges_from(sgs)
        return [
            TreeComponent(sg)
            for sg in nx.connected_component_subgraphs(g, False)
        ]

    def run(self):

        print 'num cylic:', len(self.cyclic_components)
        print 'num tree:', len(self.tree_components)

        # Munge all components into a single, randomised list. If there are any
        # cyclic components, put a random one at the start of the list.
        cyclic_comps = self.cyclic_components
        comps = cyclic_comps + self.tree_components
        #print 'num comps:', len(comps)
        #print 'comps:', comps
        random.shuffle(comps)
        if cyclic_comps:
            cyclic_comp = random.choice(cyclic_comps)
            comps.remove(cyclic_comp)
            comps.insert(0, cyclic_comp)

        for comp in comps:

            print comp#, a_points
            a_points = comp.articulation_points
            print '    ->', a_points

        # Build articulation point / component dictionary.
        connections = {}
        for comp in comps:
            for point in comp.articulation_points:
                connections.setdefault(point, []).append(comp)

        other_connections = {}
        for comp in comps:
            for point in comp.articulation_points:
                other_connections.setdefault(comp, set()).add(point)

        #print connections
        #print other_connections

        # Stitch components together.
        prev_comp = None
        while comps:
            comp = comps.pop(0)


            start_point = None
            if prev_comp is not None:
                art_points = set(comp.g) & set(prev_comp.g)
                start_point = list(art_points)[0]

            layouter = comp.layouter_cls(comp.g, self.final, start_point)
            layouter.run()

            layout = layouter.layouts[0] # TODO: Take random
            self.final.add_component(layout)

            # print '->', layout
            # print '->', type(layout)
            # print '->', list(layout.edges())
            # print '->', nx.get_edge_attributes(layout, DIRECTION)
            # for k, v in nx.get_edge_attributes(layout, DIRECTION).items():
            #     print k, '->', v

            prev_comp = comp

            # pos = nx.get_node_attributes(layout, POSITION)
            # nx.draw_networkx(layout, pos)
            # plt.show()


        pos = nx.get_node_attributes(self.final, POSITION)
        nx.draw_networkx(self.final, pos)
        plt.show()