import itertools as it
import random

import networkx as nx

from reactor.blocks.blockgraph import BlockGraph
from reactor.blocks.edgeblock import EdgeBlock
from reactor.blocks.faceblock import FaceBlock
from reactor.blocks.rootblock import RootBlock
from reactor.faceanalysis import FaceAnalysis
from reactor.layouters.facelayouter import NodeState


class Layouter(object):

    def __init__(self, g, map_):
        self._g = g
        self._map = map_

    @property
    def g(self):
        return self._g

    def _sort_nodes(self, nodes):
        """
        Sort criteria:
        - Prioritise faces
        - Priortise smaller faces
        - Sorted tuple

        """
        return sorted(nodes, key=lambda n: (len(n) < 3, len(n), sorted(n)))

    def bfs_tree(self, g, source, reverse=False, depth_limit=None, sort_neighbors=None):
        t = BlockGraph()
        t.add_node(source)
        edges_gen = nx.bfs_edges(
            g,
            source,
            reverse=reverse,
            depth_limit=depth_limit,
            sort_neighbors=sort_neighbors,
        )
        t.add_edges_from(edges_gen)
        return t

    # TODO: Make this class the actual quotient graph and make this a class
    # method.
    def get_block_graph(self):

        # Split the input graph into biconnected components. Each biconn will
        # become a node in the block graph.
        g = nx.Graph()

        # Build nodes.
        biconns = list(nx.biconnected_components(self.g))
        for biconn in biconns:
            sg = self.g.subgraph(biconn)
            if len(biconn) < 3:
                g.add_node(EdgeBlock(sg))
            else:
                for face in FaceAnalysis(sg).get_faces():
                    fsg = self.g.subgraph(face)
                    g.add_node(FaceBlock.from_path(face, fsg))

        # Build edges.
        edges = filter(lambda x: x[0].is_adjacent(x[1]), it.combinations(g, 2))
        g.add_edges_from(edges)

        # Find path from N1 to N13.
        #print(list(self.g))
        paths = nx.all_shortest_paths(self.g, 'N1', 'N13')
        for path in (['N1', 'N4', 'N3', 'N6', 'N15', 'N14', 'N13'],):#

            #print('\npath:', path)

            # Find the components that lie on this path.
            # for block in g:
            #     #print('biconn:', biconn)
            #     if set(block) & set(path):
            #         print('    overlap:', type(block), list(block))

            # NEED TO ORIENT THE PATH SO THE RELATIVITY OF THE ANGLES MAKES
            # SENSE.

            # ORIENT THE GRAPH...? Would that make things easier?

            # Find the possible angle of every node on the path. Remember that
            # these angles are relative to each other - not the world, eg STRAIGHT
            # means continue along the vector of the previous edge. The first
            # and last node angles can be anything until we figure out what
            # these nodes connect to.
            #
            # If an edge incident to a node forms the border between two faces
            # that also share edges with the path then we know the angle of the
            # node must be straight or outside.
            #
            # If a node has four incident edges, we check if the path belongs
            # to the same face. If the path falls on the same face then the
            # angle is either inside or outside, depending on the path direction.
            # If the path falls on different faces then the angle is straight.
            #prev_node = path[0]
            #for i, node in enumerate(path[:-1]):
            path = nx.path_graph(path, create_using=nx.DiGraph)#nx.DiGraph(self.g.subgraph(path))
            print('path:', list(path))
            for node in path:
                #next_node = path[i + 1]
                print('\n    node:', node)

                # Get incident edges and reorder.
                # incidents = self.g.in_edges(node) + self.g_out_edges(node)
                # for i, incident in enumerate(incidents):
                #     if incident not in path:
                #         incidents[i] = tuple(reversed(list(incident)))


                #num_incidents = len(incidents)
                #state = None
                #if num_incidents == 4:
                #    state = NodeState.KNOWN

                # Len or 1 or 2.
                # incident_edges_on_path = [
                #     incident
                #     for incident in incidents
                #     if set(path).issuperset(set(incident))
                # ]
                # from itertools import tee
                # def pairwise(iterable):
                #     "s -> (s0,s1), (s1,s2), (s2, s3), ..."
                #     a, b = tee(iterable)
                #     next(b, None)
                #     return zip(a, b)


                # *************************

                # If num incident face blocks is 1, then the node is on an edge
                # with the external face and can have angles of 90, 0, -90
                # degrees (providing the adjoining face has the number of verts
                # to allow this).

                # If the num incident face blocks is 2, then the node is on an
                # edge between two interior faces and can have angles of 90, 0,
                # -90 degrees (providing the adjoining face has the number of
                # verts to allow this).

                # If the num incident face blocks is 3, then the node is on an
                # edge between three interior faces and can have angles of 90,
                # 0 or -90 and 0. If the path is along two edges of the same
                # face then there are two possible angles (the sign coming from
                # turning left or right which is divined from the winding order
                # of the adjoining face). Look to the number of verts of each
                # adjoining face to see what angles they will allow.

                # If the num incident face blocks is 4, then we should be able
                # to divine exactly which angle the node must be. If the path
                # is contained on the same face then the angle is either 90 or
                # -90 depending on the winding order. If the path is along
                # different faces then the angle is 0.



                in_edge = next(iter(path.in_edges(node)), None)
                out_edge = next(iter(path.out_edges(node)), None)
                print('        in_edge:', in_edge)
                print('        out_edge:', out_edge)

                direction = None
                same_face = False
                node_blocks = [block for block in g if node in block]
                print('        num adj blocks:', len(node_blocks))
                for block in node_blocks:

                    # TODO: Try to get direction when in / out edge is None
                    if in_edge in block.edges_forward and out_edge in block.edges_forward:
                        #print('    INNER CORNER')
                        direction = 'clockwise'
                        same_face = True
                        break
                    elif in_edge in block.edges_reverse and out_edge in block.edges_reverse:
                        #print('    OUTER CORNER')
                        direction = 'anti-clockwise'
                        same_face = True
                        break

                # Currently direction = None == same_face = False
                print('    direction:', direction)
                print('    same_face:', same_face)
                continue

            #     # Also test that these are faces...
            #     incident_blocks = [
            #         b
            #         for b in g
            #         if set(b) & set([node])
            #     ]
            #     print('        incident_blocks:', incident_blocks)
            #
            #     for block in incident_blocks:
            #         if all([
            #             set(block).issuperset(set(edge))
            #             for edge in incident_edges_on_path
            #         ]):
            #             print('        NODE IS A CORNER:', node)
            #             print('        edges:', str(incident_edges_on_path), 'block:', str(list(block)), '->', any([edge in block for edge in incident_edges_on_path]))
            #             break
            #     else:
            #         print('        NODE IS STRAIGHT:', node)
            #
            # prev_node = node



            # Last node is unnecessary as there is no out edge...
            #print('    node:', node, 'incidents:', incidents, 'state:', state, 'incident blocks:', [str(type(b)) + ' ' + str(b) for b in incident_blocks])

        return


        # Find root node.
        sorted_nodes = self._sort_nodes(g)
        root = sorted_nodes[0]

        # Put a super root behind the root node. This will place the very first
        # node at the origin.
        super_root = RootBlock(self.g.subgraph([sorted(root)[0]]))
        g.add_edge(super_root, root)

        # Orient graph. Sort neighbours so that faces are visited first from
        # smallest to largest, then other biconns.
        g = self.bfs_tree(g, super_root, sort_neighbors=self._sort_nodes)

        # Sort nodes.
        for node in g:
            p_node = g.parent(node)
            node.sort(p_node)

        return g

    def bfs(self, g):
        blocks = list(g)
        #print('blocks:')
        #for b in blocks:
        #    #print('    ->', b)

        i = 0
        while i < len(blocks):

            layouter = g.get_layouter(blocks[i])
            if layouter.done:
                #print('SKIPPING AS DONE:', blocks[i])
                i += 1
                continue

            #print('process ->', i, blocks[i], 'parent:', g.parent(blocks[i]))
            if not layouter.permutations:# is None:
                #print('    creating new perms')
                #try:
                layouter.permutations = layouter.get_permutations(self._map.layout)
                # except:
                #     from reactor import utils
                #     pos = nx.get_node_attributes(self.layout, POSITION)
                #     utils.draw_graph(self.layout, pos)
                #     raise
                random.shuffle(layouter.permutations)
            #else:
                #print('    using existing perms')

            while layouter.permutations:
                perm = layouter.permutations.pop(0)
                if not layouter.can_lay_out(perm, self._map):
                    #print('    FAILED:', nx.get_node_attributes(perm, POSITION))
                    continue
                layouter.add_to_layout(perm, self._map.layout)
                #print('    SUCCESS:', list(perm.edges), nx.get_node_attributes(perm, POSITION))
                layouter.done = True

                i += 1
                break
            else:

                # Move the cursor back to the parent.
                parent = g.parent(blocks[i])
                #print('BACKTRACK:', blocks[i], 'TO:', parent)
                while blocks[i] != parent:
                    #print('    REWIND:', blocks[i], i)
                    i -= 1

                # Mark all blocks under the parent as not done and remove
                # their permutations.
                j = i
                while j < len(blocks):
                    olayouter = g.get_layouter(blocks[j])
                    if olayouter.done:
                        olayouter.done = False
                        if blocks[j] != blocks[i]:
                            olayouter.permutations.clear()
                            #print('    REMOVE PERMS:', blocks[j])
                    j += 1

                # Remove the failed blocks from the layout.
                rem_blocks = nx.dfs_tree(g, blocks[i])
                for block in rem_blocks:
                    olayouter = g.get_layouter(block)
                    olayouter.remove_from_layout(self._map.layout)

    def run(self):
        bg = self.get_block_graph()
        return
        self.bfs(bg)
        print('complete:', len(self.g) == len(self._map.layout))
        print('remainging:', set(self.g) - set(self._map.layout))
