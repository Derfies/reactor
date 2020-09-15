import abc


class LayouterBase(object):

    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self.layouts = []

    @abc.abstractmethod
    def run(self):
        """"""