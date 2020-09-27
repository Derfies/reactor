from reactor.blocks.cyclicblock import CyclicBlock


class RootCyclicBlock(CyclicBlock):

    pass

    # @property
    # def node(self):
    #     return self.data
    #
    # def get_permutations(self):
    #     g = nx.DiGraph()
    #     g.add_node(self.data, **{POSITION: Vector2(0, 0)})
    #     return [g]