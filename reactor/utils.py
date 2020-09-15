import random

import const
from vector import Vector2


def get_random_direction(directions=None):
    directions = directions or list(const.Direction)
    idx = random.randint(0, len(directions) - 1)
    return directions[idx]


def step(direction, length=1):
    pos = Vector2(0, 0)
    if direction == const.Direction.up:
        pos[1] += length
    elif direction == const.Direction.right:
        pos[0] += length
    elif direction == const.Direction.down:
        pos[1] -= length
    elif direction == const.Direction.left:
        pos[0] -= length
    else:
        raise Exception('Unknown direction: {}'.format(direction))
    return pos