import networkx as nx
import matplotlib.pyplot as plt

from const import POSITION, Angle
from orthogonalface import OrthogonalFace
from orthogonalgraph import OrthogonalGraph


if __name__ == '__main__':
    edges = [
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 4),
        (4, 5),
        (5, 6),
        (6, 7),
        (7, 8),
        (8, 9),
        (9, 10),
        (10, 11),
        (11, 12),
        (12, 0),
    ]
    angles = [
        Angle.inside,
        Angle.inside,
        Angle.inside,
        Angle.inside,

        Angle.outside,
        Angle.outside,
        Angle.straight,
        Angle.outside,
        Angle.outside,

        Angle.inside,
        Angle.inside,
        Angle.inside,
        Angle.inside,
    ]
    lengths = [
        3,
        2,
        1,
        1,
        1,
        #2,
        0.5,
        #2,
        3.5,
        1,
        1,
        1,
        2,
        3,
        5
    ]
    f = OrthogonalFace(edges, angles, lengths)
    g = OrthogonalGraph()
    g.add_face(f)

    pos = nx.get_node_attributes(g, POSITION)



    #grid = create_grid(g)

    nx.draw_networkx(g, nx.get_node_attributes(g, POSITION))
    plt.show()