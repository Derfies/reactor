import itertools as it
import random
import unittest

import networkx as nx
import numpy as np
from parameterized import parameterized

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

    # def get_block_state(self, wf, block):
    #
    #     # TODO: Put this function in the main module somewhere?
    #     start, stop = wf.block_to_index_range[block]
    #     block_slice = slice(start, stop)
    #     return wf.get_state((block_slice,))
    #
    # def assert_blocks_collapsed(self, wf, seed):
    #     """
    #     Assert that each
    #     """
    #     # Assert each index is collapsed.
    #     for block in wf.block_g:
    #         state = self.get_block_state(wf, block)
    #         self.assertEqual(True, wf.is_collapsed(state), f'Seed: {seed}')

    def assert_blocks_angle_sum(self, wf, seed):
        """
        Assert that all interior angles of a block add to 360.

        """
        # Assert block sum is 360.
        for block in wf.block_g:
            block_slice = wf.block_to_slice[block]
            total = np.sum(wf.get_tiles(block_slice))
            self.assertEqual(total, 360, f'Seed: {seed}')

    @parameterized.expand([
        #('../data/test1.gexf'),
        ('../data/test2.gexf'),
    ])
    def test_angle_wave_function(self, graph_path):

        # Not working out the sum of angles to 360
        for seed in range(5):
            np.random.seed(seed)
            g = self.load_graph(graph_path)
            bg = self.create_block_graph(g)
            wf = AngleWavefunction(g, bg)
            wf.run()
            wf.debug()

        self.assertTrue(wf.is_collapsed(wf.wave))
        self.assert_blocks_angle_sum(wf, seed)


if __name__ == '__main__':
    unittest.main()
