import itertools as it
import random
import unittest

import networkx as nx
import numpy as np
from parameterized import parameterized

from reactor.blocks.edgeblock import EdgeBlock
from reactor.blocks.faceblock import FaceBlock
from reactor.faceanalysis import FaceAnalysis
from reactor.wfc.anglewavefunction import AngleWaveFunction
from reactor.readers.gexfreader import GEXFReader


random.seed(1)


class TestAngleWaveFunction(unittest.TestCase):

    def load_graph(self, path):
        return GEXFReader()(path).to_undirected()

    def create_block_graph(self, g):

        # TODO: Remove this duplicate code from layouter.py
        # Split the input graph into biconnected components. Each biconn will
        # become a node in the block graph.
        bg = nx.Graph()

        # Build nodes.
        biconns = list(nx.biconnected_components(g))
        for biconn in biconns:
            sg = g.subgraph(biconn)
            if len(biconn) < 3:
                bg.add_node(EdgeBlock(sg))
            else:
                for face in FaceAnalysis(sg).get_faces():
                    fsg = g.subgraph(face)
                    bg.add_node(FaceBlock.from_path(face, fsg))

        # Build edges.
        edges = filter(lambda x: x[0].is_adjacent(x[1]), it.combinations(bg, 2))
        bg.add_edges_from(edges)
        return bg

    @parameterized.expand([
        '../data/quadrilateral.gexf',
        '../data/pentagon.gexf',
        '../data/hexagon.gexf',
        '../data/grid2.gexf',
        '../data/test10.gexf',
        '../data/test1.gexf',
        '../data/test2.gexf',
    ])
    def test_angle_wave_function(self, graph_path):

        # Not working out the sum of angles to 360
        #for seed in range(57, 61):
        for seed in range(10):
            np.random.seed(seed)
            g = self.load_graph(graph_path)
            bg = self.create_block_graph(g)
            wf = AngleWaveFunction(g, bg)
            wf.run()
            wf.debug(wf.wave, title=f'FINAL [{seed}]:')

            self.assertTrue(wf.is_collapsed(wf.wave))
            for array in wf.index_to_block_array.values():
                wf.check_sum_block_angle(array)
            for array in wf.index_to_node_array.values():
                wf.check_sum_node_angle(array)


if __name__ == '__main__':
    unittest.main()
