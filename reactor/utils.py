import os
import random

import matplotlib.pyplot as plt
import networkx as nx
from simple_settings import settings

from reactor import const
from reactor.blocks.faceblock import FaceBlock
from reactor.const import POSITION, WEIGHT, WIDTH
from reactor.geometry.rect import Rect
from reactor.geometry.vector import Vector2
from reactor.orthogonalface import OrthogonalFace
from reactor.map import Map


MAP_SIZE = (10, 10)


def get_node_position(g, node):
    return g.nodes[node].get(const.POSITION)


def get_edge_positions(g, edge):
    return (
        get_node_position(g, edge[0]),
        get_node_position(g, edge[1])
    )


def get_edge_rect(g, edge):
    rect = Rect(*get_edge_positions(g, edge))
    rect.normalise()
    edge_weight = g.edges[edge].get(WEIGHT, 1)
    edge_settings = settings.EDGE_WEIGHTS[edge_weight]
    edge_width = edge_settings.get(WIDTH, 1)
    rect.inflate(edge_width / 2.0)
    return rect


def get_edge_rects(g):
    return [get_edge_rect(g, edge) for edge in g.edges]


def get_random_direction(directions=None):
    directions = directions or list(const.Direction)
    idx = random.randint(0, len(directions) - 1)
    return directions[idx]


def step(direction, length=1):
    pos = Vector2(0, 0)
    if direction == const.Direction.UP:
        pos[1] += length
    elif direction == const.Direction.RIGHT:
        pos[0] += length
    elif direction == const.Direction.DOWN:
        pos[1] -= length
    elif direction == const.Direction.LEFT:
        pos[0] -= length
    else:
        raise Exception('Unknown direction: {}'.format(direction))
    return pos


def init_pyplot(figsize):
    #import matplotlib as mpl
    #mpl.style.use('classic')

    # Set pyplot dimensions.
    plt.figure(figsize=figsize)

    #plt.minorticks_on()
    #plt.majorticks_on()
    #fig, ax = plt.subplots(figsize=figsize)

    # Then we set up our axes (the plot region, or the area in which we plot
    # things). Usually there is a thin border drawn around the axes, but we turn
    # it off with `frameon=False`. Also set the aspect ratio so x and y units
    # appear the same size.

    ax = plt.axes(frameon=False)
    ax.tick_params(left=True, bottom=True, labelleft=True, labelbottom=True)
    #ax.set_xticks(numpy.arange(0, 1, 0.1))
    #ax.set_yticks(numpy.arange(0, 1., 0.1))
    #ax.grid(True)
    ax.set_aspect('equal')

    # Even though our axes (plot region) are set to cover the whole image with
    # [0,0,1,1], by default they leave padding between the plotted data and the
    # frame. We use tigher=True to make sure the data gets scaled to the full
    # extents of the axes.
    plt.tight_layout()
    #plt.autoscale(tight=True)
    #return


def draw_rect(rect, **kwargs):
    """Converts a rect to a graph so it can be drawn."""
    face = FaceBlock.from_path((1, 2, 3, 4))
    angles = {n: const.Angle.INSIDE for n in face}
    lengths = {}
    lengths[(1, 2)] = lengths[(3, 4)] = rect.height
    lengths[(2, 3)] = lengths[(4, 1)] = rect.width
    direction = const.Direction.UP
    g = OrthogonalFace(face, angles, lengths, direction, rect.p1)
    kwargs['pos'] = g.node_positions
    nx.draw_networkx(g, **kwargs)


def draw_map(map_, save_path=None):
    pos = nx.get_node_attributes(map_.layout, POSITION)
    if not pos:
        pos = nx.planar_layout(map_.layout)
    init_pyplot(MAP_SIZE)

    # Draw the map.
    edge_weights = [
        map_.layout.edges[edge].get(WEIGHT, 1)
        for edge in map_.layout.edges
    ]
    nx.draw_networkx(map_.layout, pos=pos, width=edge_weights)
    for room in map_.rooms:
        draw_rect(room, node_size=0, with_labels=False, arrows=False,
                  edge_color='grey', width=4)

    # Test drawing thick edges.
    for edge_rect in get_edge_rects(map_.layout):
        draw_rect(edge_rect, node_size=0, with_labels=False, arrows=False,
                  edge_color='green', width=1)

    # Fix up axes ticks.
    ax = plt.axes(frameon=False)
    ax.tick_params(left=True, bottom=True, labelleft=True, labelbottom=True)

    # Show window or save to disk.
    if save_path is None:
        plt.show()
    else:
        dir_path = os.path.split(save_path)[0]
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path)
        plt.savefig(save_path)


def draw_graph(g):
    map_ = Map()
    map_.layout = g
    draw_map(map_)
