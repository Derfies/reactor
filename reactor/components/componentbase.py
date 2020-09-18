import abc


class ComponentBase(object):

    __metaclass__ = abc.ABCMeta

    layouter_cls = None

    def __init__(self, g):
        self.g = g
        assert self.layouter_cls is not None, 'requires layouter class'

    @abc.abstractproperty
    def articulation_points(self):
        """"""