import enum


ANGLE = 'angle'
DIRECTION = 'direction'
POSITION = 'position'
LENGTH = 'length'


class Angle(enum.IntEnum):

    INSIDE = 90
    OUTSIDE = -90
    STRAIGHT = 0


class Direction(enum.IntEnum):

    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3

    @staticmethod
    def normalise(direction):
        return Direction(direction % 4)

    @staticmethod
    def opposite(direction):
        return Direction.normalise(direction - 2)

    @staticmethod
    def xs():
        return Direction.LEFT, Direction.RIGHT

    @staticmethod
    def ys():
        return Direction.UP, Direction.DOWN
