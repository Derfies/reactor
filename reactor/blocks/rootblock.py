from reactor.blocks.blockbase import BlockBase


class RootBlock(BlockBase):

    def __str__(self):
        return 'ROOT:' + str(list(self.nodes))
