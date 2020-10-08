import networkx as nx
from networkx.algorithms.minors import _quotient_graph
from networkx.utils import arbitrary_element

from reactor.blocks.cyclicblock import CyclicBlock
from reactor.blocks.nodeblock import NodeBlock
from reactor.blocks.rootcyclicblock import RootCyclicBlock
from reactor.blocks.rootnodeblock import RootNodeBlock
from reactor.embeddedbiconngraph import EmbeddedBiconnGraph


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
        self._dg = nx.DiGraph()
        self._q = nx.DiGraph()   # Adj order is important!

    @property
    def g(self):
        return self._g

    @property
    def biconns(self):
        return self._biconns

    # @property
    # def dg(self):
    #     return self._dg

    @property
    def q(self):
        return self._q

    @property
    def root(self):
        return next(filter(lambda n: not self.q.in_edges(n), self.q))

    def get_block_class(self, block):
        return self.q.nodes[block].get(LAYOUT_CLASS)
    '''
    def _calculate_oriented_graph(self):

        # Use a node from the largest biconnected component as the source. This
        # will hopefully process a larger chunk of faces / permutations first.
        biconns = sorted(self.biconns, key=lambda b: (len(b), b), reverse=True)

        source = None
        if biconns:
            source = sorted(biconns[0])[0]

        # BROKEN - this source isn't working!!!

        # TODO: Do we still need to do this anymore?
        # Yes? because dfs on the resulting quotient graph is going to be hard
        # Yes? Because each block still needs to know it's parent
        # dg = self.g.to_directed()
        # edge_dfs = list(nx.edge_dfs(self.g, source))#, 'N5')) # HAXXOR
        # del_edges = filter(lambda e: e not in edge_dfs, dg.edges())
        # dg.remove_edges_from(del_edges)

        # TODO: Bow graphs do not work. They share a node but they're ending up
        # in two different frozen sets.
        # NO
        dg = nx.dfs_tree(self.g, source)

        return dg
    '''

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
        self._q = self._calculate_quotient_graph()

        biconns_to_face_g = {}
        q_nodes = sorted(self.q)
        for q_node in q_nodes:
            if q_node not in self.biconns:
                pass
                #self.q.nodes[q_node][LAYOUT_CLASS] = NodeBlock
                #nx.relabel_nodes(self.q, {q_node: list(q_node)[0]}, copy=False)
            else:

                # Run face detection and merge the resulting graph into the
                # main graph.
                bg = EmbeddedBiconnGraph(self.g.subgraph(q_node))
                bg.run()
                face_g = biconns_to_face_g[q_node] = bg.get_face_graph()
                #nx.set_node_attributes(face_g, CyclicBlock, LAYOUT_CLASS)
                self.q.update(face_g)

                # Find adjacent edges in the biconn and find out which faces
                # they hook into. These should all be single nodes or else they
                # would be inside *this* biconn. This may change with bow ties
                # however.
                for nbr in self.q.neighbors(q_node):
                    for face in face_g:

                        # There should be only one edge between this biconn's
                        # face and on original neighbour in the quotient graph,
                        # otherwise they would have been in the same biconn.
                        # Again... bow-ties...
                        edge = next(nx.edge_boundary(self.g, face, nbr), None)
                        if edge is not None:
                            self.q.add_edge(face, nbr)

                # Remove the original biconn from the graph.
                self.q.remove_node(q_node)

        # Find root node.
        # Use the smallest face from the largest biconn.
        root_node = q_nodes[0]
        if biconns_to_face_g:
            largest_biconn = sorted(biconns_to_face_g, key=lambda b: len(b))[0]
            root_node = sorted(biconns_to_face_g[largest_biconn], key=lambda f: len(f))[0]





        # Now orient the graph.
        self._q = nx.bfs_tree(self.q, root_node)

        # Create root node if necessary.
        # DO THIS FOR ALL ROOT CYCLES
        '''
        if len(root_node) > 1:
            new_root_node = sorted(root_node)[0]
            new_root_node = frozenset([new_root_node])
            self.q.add_edge(new_root_node, root_node)
            root_node = new_root_node
        print('\nroot_node:', root_node)
        '''

        for node in list(self.q):

            if len(node) > 1:
                if node == root_node:
                    new_root_node = sorted(root_node)[0]
                    new_root_node = frozenset([new_root_node])
                    self.q.add_edge(new_root_node, root_node)
                    root_node = new_root_node
                else:
                    p_node = next(self.q.predecessors(node), None)
                    if len(p_node) < 2:
                        print('*****do:', node)
                        pp_node = list(p_node)[0]
                        edge = next(nx.edge_boundary(self.g, node, (pp_node,)), None)
                        face_root = list(filter(lambda n: n != pp_node, edge))[0]
                        print('p_node:', p_node)
                        print('face_root:', face_root)
                        self.q.remove_edge(p_node, node)
                        nx.add_path(self.q, (p_node, frozenset([face_root]), node))
                        #self.q.add_edge(new_root_node, root_node)
                        # print('face_root', face_root)
                        #
                        # out_edge = list(node.out_edges(face_root))[0]
                        # print('out_edge', out_edge)
                        # node.set_source_edge(out_edge)

        print('\nroot_node:', root_node)


        # Assign layout classes.
        for node in self.q:
            p_node = next(self.q.predecessors(node), None)
            if p_node is None:
                self.q.nodes[node][LAYOUT_CLASS] = RootNodeBlock
            elif len(node) > 1:
                if len(p_node) > 1:
                    self.q.nodes[node][LAYOUT_CLASS] = CyclicBlock
                else:
                    self.q.nodes[node][LAYOUT_CLASS] = RootCyclicBlock
            else:
                self.q.nodes[node][LAYOUT_CLASS] = NodeBlock


            # Set face leading edge.
            # HAXXOR
            if len(node) > 1:
                print('node:', node)
                print('p_node:', p_node)
                if len(p_node) > 1:
                    print('parent was face')
                    #print(node.edges, p_node.edges)
                    common = set(node.edges_forward()) & set(p_node.edges_reverse())
                    out_edge = list(common)[0]
                    node.set_source_edge(out_edge)
                    print('set_source_edge:', out_edge)
                else:

                    # Issue happens if the previous node is a root node, ie it
                    # falls on this face. As distict from an edges leading INTO
                    # the face.
                    print('parent was node')
                    #print('is leading from node')
                    p_node = list(p_node)[0]

                    if p_node in node:
                        out_edge = list(node.out_edges(p_node))[0]
                        #print('----->', list(node.edges()), out_edge)
                        print('set_source_edge:', out_edge)
                        node.set_source_edge(out_edge)
                        #print('NOW:', node.get_source_edge())
                    # else:
                    #     print('SHOULD NEVER GET HERE')
                    #
                    #     # Set the start edge to be the one that
                    #     edge = next(nx.edge_boundary(self.g, node, (p_node,)), None)
                    #     face_root = list(filter(lambda n: n != p_node, edge))
                    #     print('face_root', face_root)
                    #
                    #     out_edge = list(node.out_edges(face_root))[0]
                    #     print('out_edge', out_edge)
                    #     node.set_source_edge(out_edge)


        for node in list(self.q):
            print(node, type(node), '->', self.q.nodes[node].get(LAYOUT_CLASS))
