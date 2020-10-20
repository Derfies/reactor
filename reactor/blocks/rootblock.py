from reactor.blocks.blockbase import BlockBase


class RootBlock(BlockBase):

    def __str__(self):
        return 'ROOT:' + str(list(self.nodes))

    # TODO: Find out why this class isn't failing since it hasn't fulfilled its
    # abstract contract.