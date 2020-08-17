import networkx as nx
import matplotlib.pyplot as plt

from const import POSITION
from mapgenerator import MapGenerator


GRID_PATH = 'data/grid2.graphml'


def init_pyplot(figsize):

    # Set pyplot dimensions.
    plt.figure(figsize=figsize)

    # Then we set up our axes (the plot region, or the area in which we plot things).
    # Usually there is a thin border drawn around the axes, but we turn it off with `frameon=False`.
    ax = plt.axes([0, 0, 1, 1], frameon=False)

    # Then we disable our xaxis and yaxis completely. If we just say
    # plt.axis('off'), they are still used in the computation of the image
    # padding.
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)

    # Even though our axes (plot region) are set to cover the whole image with
    # [0, 0, 1, 1], by default they leave padding between the plotted data and
    # the frame. We use tigher=True to make sure the data gets scaled to the
    # full extents of the axes.
    plt.autoscale(tight=True)


if __name__ == '__main__':

    # Initialise a map generator using a path to a node graph file, then run it.
    map_gen = MapGenerator(GRID_PATH)
    map_gen.run()

    # Draw output.
    for i in range(len(map_gen.layouters)):
        nx.draw_networkx(map_gen.biconns[i].g, map_gen.biconns[i].pos)
        plt.show()
        for graph in map_gen.layouters[i].graphs:
            pos = nx.get_node_attributes(graph, POSITION)
            nx.draw_networkx(graph, pos)
            plt.show()