import os
import random

import networkx as nx
import matplotlib.pyplot as plt

from reactor import const
from reactor.geometry.vector import Vector2


def get_node_position(g, node):
    return g.nodes[node].get(const.POSITION)


def get_edge_positions(g, edge):
    return (
        get_node_position(g, edge[0]),
        get_node_position(g, edge[1])
    )


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


def draw_graph(g, pos=None):
    if pos is None:
        pos = nx.planar_layout(g)#, prog='neato')
    init_pyplot((5, 5))
    nx.draw_networkx(g, pos=pos)
    ax = plt.axes(frameon=False)
    ax.tick_params(left=True, bottom=True, labelleft=True, labelbottom=True)
    plt.show()


def save_graph(g, pos=None, save_path=None):
    if pos is None:
        pos = nx.nx_agraph.graphviz_layout(g, prog='neato')
    init_pyplot((10, 10))
    nx.draw_networkx(g, pos=pos)
    dir_path = os.path.split(save_path)[0]
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)
    plt.savefig(save_path)