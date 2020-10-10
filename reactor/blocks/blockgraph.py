import networkx as nx
from networkx.algorithms.minors import _quotient_graph
from networkx.utils import arbitrary_element

from reactor.blocks.cyclicblock import CyclicBlock
from reactor.blocks.nodeblock import NodeBlock
from reactor.blocks.rootcyclicblock import RootCyclicBlock
from reactor.blocks.rootnodeblock import RootNodeBlock
from reactor.faceanalysis import FaceAnalysis


LAYOUT_CLASS = 'class'


# Can probably remove this now.
def equivalence_classes(iterable, relation):
    """Returns the set of equivalence classes of the given `iterable` under
    the specified equivalence relation.

    `relation` must be a Boolean-valued function that takes two argument. It
    must represent an equivalence relation (that is, the relation induced by
    the function must be reflexive, symmetric, and transitive).

    The return value is a set of sets. It is a partition of the elements of
    `iterable`; duplicate elements will be ignored so it makes the most sense
    for `iterable` to be a :class:`set`.

    """
    # For simplicity of implementation, we initialize the return value as a
    # list of lists, then convert it to a set of sets at the end of the
    # function.
    blocks = []
    # Determine the equivalence class for each element of the iterable.
    for y in iterable:
        # Each element y must be in *exactly one* equivalence class.
        #
        # Each block is guaranteed to be non-empty
        for block in blocks:
            x = arbitrary_element(block)
            if relation(x, y):
                block.append(y)
                break
        else:
            # If the element y is not part of any known equivalence class, it
            # must be in its own, so we create a new singleton equivalence
            # class for it.
            blocks.append([y])

    # HAXXOR
    seen = set()
    seen_add = seen.add
    frozen_sets = []
    for block in blocks:
        frozen_set = frozenset(block)
        if not (frozen_set in seen or seen_add(frozen_set)):
            frozen_sets.append(frozen_set)
    return frozen_sets


class BlockGraph(object):

    def __init__(self, g):
        self._g = g
        self._biconns = ()

    @property
    def g(self):
        return self._g

    @property
    def biconns(self):
        return self._biconns

    def _calculate_quotient_graph(self):

        # TODO: This still puts a bow into two separate groups :(
        def partition_fn(a, b):
            return any([
                a in biconn and b in biconn and len(biconn) > 2
                for biconn in self.biconns
            ])
        partition = equivalence_classes(self.g, partition_fn)
        return _quotient_graph(self.g, partition)

    # TODO: Make this class the actual quotient graph and make this a class
    # method.
    def run(self):
        self._biconns = tuple(nx.biconnected_components(self.g))
        q = self._calculate_quotient_graph()

        biconns_to_face_g = {}
        q_nodes = sorted(q)
        for q_node in q_nodes:
            if q_node not in self.biconns:
                continue

            # Run face detection and merge the resulting graph into the
            # main graph.
            bg = FaceAnalysis(self.g.subgraph(q_node))
            face_g = biconns_to_face_g[q_node] = bg.get_face_graph()
            q.update(face_g)

            # Find adjacent edges in the biconn and find out which faces
            # they hook into. These should all be single nodes or else they
            # would be inside *this* biconn. This may change with bow ties
            # however.
            for nbr in q.neighbors(q_node):
                for face in face_g:

                    # There should be only one edge between this biconn's
                    # face and on original neighbour in the quotient graph,
                    # otherwise they would have been in the same biconn.
                    # Again... bow-ties...
                    edge = next(nx.edge_boundary(self.g, face, nbr), None)
                    if edge is not None:
                        q.add_edge(face, nbr)

            # Remove the original biconn from the graph.
            q.remove_node(q_node)

        # Find root node.
        # Use the smallest face from the largest biconn.
        # TODO: Root node not deterministic. Does this matter?
        root_node = q_nodes[0]
        if biconns_to_face_g:
            largest_biconn = sorted(biconns_to_face_g, key=lambda b: len(b))[0]
            root_node = sorted(biconns_to_face_g[largest_biconn], key=lambda f: len(f))[0]

        print('root_node:', root_node)

        # Now orient the graph.
        q = nx.bfs_tree(q, root_node)
        q._graph = self.g

        # Put new root node behind first node / first cycles.
        for node in list(q):
            if len(node) > 1:
                if node == root_node:
                    new_root_node = sorted(root_node)[0]
                    new_root_node = frozenset([new_root_node])
                    q.add_edge(new_root_node, root_node)
                    root_node = new_root_node
                else:
                    p_node = next(q.predecessors(node), None)
                    if len(p_node) < 2:
                        pp_node = list(p_node)[0]
                        edge = next(nx.edge_boundary(self.g, node, (pp_node,)), None)
                        face_root = list(filter(lambda n: n != pp_node, edge))[0]
                        q.remove_edge(p_node, node)
                        nx.add_path(q, (p_node, frozenset([face_root]), node))

        # Set face leading edge.
        for node in q:
            p_node = next(q.predecessors(node), None)
            if len(node) > 1:
                if len(p_node) > 1:
                    common = set(node.edges_forward()) & set(p_node.edges_reverse())
                    out_edge = list(common)[0]
                    node.set_source_edge(out_edge)
                else:

                    # Issue happens if the previous node is a root node, ie it
                    # falls on this face. As distict from an edges leading INTO
                    # the face.
                    p_node = list(p_node)[0]
                    if p_node in node:
                        out_edge = list(node.out_edges(p_node))[0]
                        node.set_source_edge(out_edge)

        # Assign layout classes.
        node_classes = {}
        for node in list(q):
            layout_cls = None
            p_node = next(q.predecessors(node), None)
            if p_node is None:
                layout_cls = RootNodeBlock
            elif len(node) > 1:
                if len(p_node) > 1:
                    layout_cls = CyclicBlock
                else:
                    layout_cls = RootCyclicBlock
            else:
                layout_cls = NodeBlock

            layout = layout_cls(node, q)
            node_classes[node] = layout

        nx.relabel_nodes(q, node_classes, copy=False)

        root = next(filter(lambda n: not q.in_edges(n), q))
        return q
