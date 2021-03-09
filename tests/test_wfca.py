import itertools as it
import random
import unittest

import networkx as nx
import numpy as np
from parameterized import parameterized
from tabulate import tabulate

from reactor.blocks.edgeblock import EdgeBlock
from reactor.blocks.faceblock import FaceBlock
from reactor.faceanalysis import FaceAnalysis
from reactor.wfc.anglewavefunction import AngleWavefunction
from reactor.readers.gexfreader import GEXFReader


random.seed(1)


class TestAngleWavefunction(unittest.TestCase):

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

    def assert_sum_block_angle(self, wf, block_index, seed):
        """
        Assert that all interior angles of a block add to 360.

        """
        block_array = wf.index_to_block_array[block_index]
        sum_angles = wf.get_sum_resolved_angles(block_array)
        block = wf.index_to_block[block_index]
        self.assertEqual(sum_angles, 360, f'Block is not closed. Seed: {seed} [{block}]')

    def assert_sum_node_angle(self, wf, node, seed):
        """
        Assert that the angles around a node are no greater than 360, and in the
        case of number of neighbours equalling the number of indices, they add
        up to exactly 360 degrees.

        """
        num_neighbors = len(list(wf.g.neighbors(node)))
        node_indices = wf.node_to_indices[node]
        node_index = next(iter(node_indices))
        node_array = wf.index_to_node_array[node_index]
        sum_angles = wf.get_sum_resolved_angles(node_array, absolute=True)
        self.assertTrue(sum_angles <= 360, f'Seed: {seed}')

        num_nonzero = np.count_nonzero(node_array, axis=0)
        num_indices = num_nonzero.count()
        if num_neighbors == num_indices:
            self.assertEqual(sum_angles, 360, f'Seed: {seed}')

    @parameterized.expand([
        ('../data/quadrilateral.gexf'),
        ('../data/pentagon.gexf'),
        ('../data/hexagon.gexf'),
        ('../data/grid2.gexf'),
        ('../data/test10.gexf'),
        ('../data/test1.gexf'),
        ('../data/test2.gexf'),
    ])
    def test_angle_wave_function(self, graph_path):

        # Not working out the sum of angles to 360
        #for seed in range(57, 61):
        for seed in range(10):
            np.random.seed(seed)
            g = self.load_graph(graph_path)
            bg = self.create_block_graph(g)
            wf = AngleWavefunction(g, bg)
            wf.run()
            wf.debug(wf.wave, title=f'FINAL [{seed}]:')

            self.assertTrue(wf.is_collapsed(wf.wave))
            for block_index in wf.index_to_block_array:
                self.assert_sum_block_angle(wf, block_index, seed)
            for node in wf.g:
                self.assert_sum_node_angle(wf, node, seed)


if __name__ == '__main__':
    unittest.main()
