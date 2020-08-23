import networkx as nx
import matplotlib.pyplot as plt

from const import POSITION, Direction, DIRECTION
from mapgenerator import MapGenerator


GRID_PATH = 'data/test1.graphml'


def subdivide(list_):
    divided = []
    for i in range(len(list_)):
        divided.append(list_[i])
        if i < len(list_) - 1:
            divided.append(float(list_[i] + list_[i + 1]) / 2.0)
    return divided


def create_grid(g):

    # Build a grid to contain the graph.
    g = nx.Graph()
    xs = subdivide(sorted(set([p[0] for p in pos.values()])))
    ys = subdivide(sorted(set([p[1] for p in pos.values()])))

    for x in range(len(xs)):
        for y in range(len(ys)):
            node_name = str(xs[x]) + ', ' + str(ys[y])
            g.add_node(node_name)
            g.nodes[node_name][POSITION] = (xs[x], ys[y])

            if y:
                last_node_name = str(xs[x]) + ', ' + str(ys[y - 1])
                g.add_edge(node_name, last_node_name)
                #g.edges[(node_name, last_node_name)][DIRECTION] = (xs[x], ys[y])

            if x:
                last_node_name = str(xs[x - 1]) + ', ' + str(ys[y])
                g.add_edge(node_name, last_node_name)

    # Connect edge nodes to a 3D node
    edge_nodes = filter(lambda x: len(g.edges(x)) < 4, g.nodes())
    for edge_node in edge_nodes:
        g.add_edge('ORIGIN', edge_node)

    g.nodes['ORIGIN'][POSITION] = (3.5, 5)

    return g


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

    '''

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
    
    '''
    import enum
    from intervaltree import IntervalTree, Interval

    # Test biconn exit strategy
    from orthogonalface import OrthogonalFace
    from orthogonalgraph import OrthogonalGraph
    from const import Angle, Direction, DIRECTION

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



    grid = create_grid(g)

    nx.draw_networkx(grid, nx.get_node_attributes(grid, POSITION))
    plt.show()

    #raise

    class EventType(enum.Enum):

        BEGIN = 0
        END = 1


    class Event(object):

        def __init__(self, type_, y1, y2):
            self.type = type_
            #self.edge = edge
            #self.pos = pos
           # self.x = x
            self.y1 = y1
            self.y2 = y2

    # Collect intervals.
    events = {}
    for edge in g.edges():

        x1, y1 = pos[edge[0]]
        x2, y2 = pos[edge[1]]

        min_y, max_y = y1, y2
        if min_y > max_y:
            min_y, max_y = max_y, min_y

        if g.edges[edge][DIRECTION] == Direction.up:
            events.setdefault(x1, []).append(Event(EventType.BEGIN, min_y, max_y))
        elif g.edges[edge][DIRECTION] == Direction.down:
            events.setdefault(x1, []).append(Event(EventType.END, min_y, max_y))

    cut_node = '1.5, 1.0'#'3.0, 1.0':

    # Construct interval tree
    tree = IntervalTree()
    for t in sorted(events):
        print '\nt:', t
        for event in events[t]:
            i = Interval(event.y1, event.y2, t)
            if event.type == EventType.BEGIN:
                tree.add(i)
            elif event.type == EventType.END:
                tree.slice(i.begin)
                tree.slice(i.end)
                for overlap in tree.overlap(i):
                    print '    overlap:', overlap

                    for node in list(grid.nodes()):
                        node_pos = grid.nodes[node][POSITION]
                        node_within_x = overlap.data <= node_pos[0] <= t
                        node_within_y = overlap.begin <= node_pos[1] <= overlap.end
                        if node_within_x and node_within_y and node != cut_node:
                            grid.remove_node(node)

                tree.chop(i.begin, i.end)
        print '    final tree:', tree

    #print 'end', tree





    nx.draw_networkx(g, pos)
    #plt.show()

    nx.draw_networkx(grid, nx.get_node_attributes(grid, POSITION), node_color='blue')


    path = nx.shortest_path(grid, 'ORIGIN', cut_node)
    subg = nx.Graph(grid.subgraph(path))
    subg.remove_node('ORIGIN')
    nx.draw_networkx(subg, nx.get_node_attributes(subg, POSITION),
                     node_color='green')

    plt.show()