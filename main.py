import networkx as nx
import matplotlib.pyplot as plt

from const import POSITION
from mapgenerator import MapGenerator


GRID_PATH = 'data/reactor02.graphml'


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

    for tree in map_gen.trees:
        pos = nx.get_node_attributes(tree.g, POSITION)
        nx.draw_networkx(tree.g, pos)
        plt.show()