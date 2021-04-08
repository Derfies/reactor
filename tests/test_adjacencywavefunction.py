import random
import unittest

import numpy as np

from reactor.wfc.adjacencywavefunction import AdjacencyWaveFunction
from reactor.wfc.wavefunctionbase import Contradiction


random.seed(1)
np.random.seed(0)


class TestAdjacencyWaveFunction(unittest.TestCase):

    def test_contradiction(self):
        compatibilities = {}
        shape = (1, 2)
        weights = {'A': 1}
        wf = AdjacencyWaveFunction(compatibilities, shape, weights)
        with self.assertRaises(Contradiction):
            wf.run()

    def test_(self):
        compatibilities = {}
        shape = (1, 2)
        weights = {'A': 1}
        wf = AdjacencyWaveFunction(compatibilities, shape, weights)
        with self.assertRaises(Contradiction):
            wf.run()


if __name__ == '__main__':
    unittest.main()
