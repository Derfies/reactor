import networkx as nx
import matplotlib.pyplot as plt

from const import POSITION
from components.treecomponent import TreeComponent
from components.cycliccomponent import CyclicComponent


class MapGenerator(object):

    def __init__(self, grid_path):
        self.g = nx.Graph(nx.read_graphml(grid_path))

        self.biconns = []
        self.layouters = []
        self.trees = []

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

        final = nx.Graph()

        comps = self.cyclic_components + self.tree_components

        # Build articulation point / component dictionary.
        connections = {}
        for comp in comps:
            for point in comp.articulation_points:
                connections.setdefault(point, []).append(comp)

        while comps:
            comp = comps.pop()
            comp.layout()
            final = nx.compose(final, comp.layouter.layouts[0]) # TODO: Take random

            pos = nx.get_node_attributes(comp.layouter.layouts[0], POSITION)
            nx.draw_networkx(comp.layouter.layouts[0], pos)
            plt.show()


        pos = nx.get_node_attributes(final, POSITION)
        nx.draw_networkx(final, pos)
        plt.show()
        '''

        # pick the first component
        # lay it out
        # look at articulation points
        # run components attached to those

        #biconns = list(nx.biconnected_component_subgraphs(self.g))
        #yads = filter(lambda s: len(s) < 3, biconns)


        #print 'all A POINTS', list(nx.articulation_points(self.g))
        #print 'NOT A POINTS:', set(self.g.nodes()) - set(nx.articulation_points(self.g))



        for g in self.cyclic_components:
            print 'cyclic:', list(g), g.articulation_points
        #     a = CyclicComponent(self.g, g)
        #     print 'cyclic:', a, list(a)
        #     print '    a points:', a.articulation_points()
        #
        for g in self.tree_components:
            #b = TreeComponent(self.g, g)
            print 'tree:', list(g), g.articulation_points

        connections = {}
        for comp in self.cyclic_components + self.tree_components:
            print list(comp)
            for point in comp.articulation_points:
                print '    p:', point
                connections.setdefault(point, []).append(comp)

        print connections
        #     print 'nodes:', list(b)
        #     nodes = set(nx.articulation_points(self.g)) & set(b.nodes())
        #     print 'nodes:', nodes
        #     baz = []
        #     for node in nodes:
        #         neighbors = set(self.g.neighbors(node))
        #         neighbors.add(node)
        #         if not set(b.nodes()).issuperset(neighbors):
        #             baz.append(node)
        #
        #     print 'final:', baz
        # #     print 'tree:', b, list(b)
        # #     print '    a points:', b.articulation_points()

        return

        # print 'cyclic_nodes:', self.cyclic_nodes
        # print 'cyclic_articulation_nodes:', self.cyclic_articulation_nodes
        #
        # p = nx.shortest_path(self.g)
        # for start_node in self.cyclic_articulation_nodes:
        #     for end_node in self.cyclic_articulation_nodes:
        #         if start_node == end_node:
        #             continue
        #         print start_node, '->', end_node, ':', p[start_node][end_node]
        # for k, v in p.items():
        #     print k, v

        #return
        # cyclic_nodes = set([
        #     node
        #     for cyclic_component in self.cyclic_components
        #     for node in cyclic_component
        # ])
        # print list(cyclic_nodes)
        # print set(nx.articulation_points(self.g)) & set(cyclic_nodes)
        # return
        for cyclic_component in self.cyclic_components:

            # Try to run the planar layout on the bicon component. If this fails
            # show the layout for debug.
            bg = EmbeddedBiconnGraph(cyclic_component)
            self.biconns.append(bg)
            try:
                bg.run()
            except nx.exception.NetworkXException:
                nx.draw_networkx(bg.g, bg.pos)
                plt.show()
                raise

            ol = OrthogonalLayouter(bg.faces)
            ol.run()

            self.layouters.append(ol)

        for tree_component in self.tree_components:
            map_gen = TreeLayouter(tree_component)
            self.trees.append(map_gen)
            try:
                map_gen.run()
            except Exception, e:
                pos = nx.get_node_attributes(map_gen.g, POSITION)
                nx.draw_networkx(map_gen.g, pos)
                plt.show()
                raise
        
        '''