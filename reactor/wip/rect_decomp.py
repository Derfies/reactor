import math
import functools
from collections import namedtuple

from intervaltree import IntervalTree, Interval


class Vertex:

    def __init__(self, point, path, index, concave):
        self.point = point
        self.path = path
        self.index = index
        self.concave = concave
        self.next = None
        self.prev = None
        self.visited = False


IntervalData = namedtuple('IntervalData', [
    'start',
    'end',
    'direction',
    'data'
])


# # TODO: Replace with Interval?
# class Segment:
#
#     def __init__(self, start, end, direction):
#         a = start.point[direction ^ 1]
#         b = end.point[direction ^ 1]
#         if a < b:
#             self[0] = a
#             self[1] = b
#         else:
#             self[0] = b
#             self[1] = a
#         self.start = start
#         self.end = end
#         self.direction = direction
#         self.number = -1


def test_segment(a, b, tree, direction):
    ax = a.point[direction ^ 1]
    bx = b.point[direction ^ 1]

    for s in tree.at(a.point[direction]):
        x = s.start.point[direction ^ 1]
        if ax < x < bx:
            return False
    return True


def get_diagonals(vertices, paths, direction, tree):
    concave = [
        v
        for v in vertices
        if v.concave
    ]

    def sorted_by(a, b):
        d = a.point[direction] - b.point[direction]
        if d:
            return d
        return a.point[direction ^ 1] - b.point[direction ^ 1]
    cmp = functools.cmp_to_key(sorted_by)
    concave.sort(key=cmp)

    diagonals = []
    for i in range(len(concave)):
        a = concave[i - 1]
        b = concave[i]
        if a.point[direction] == b.point[direction]:
            if a.path == b.path:
                n = paths[a.path].length
                d = (a.index - b.index + n) % n
                if d == 1 or d == n - 1:
                    continue

            if test_segment(a, b, tree, direction):

                # Check orientation of diagonal.
                diagonals.append(Segment(a, b, direction))

    return diagonals


# Find all crossings between diagonals
def find_crossings(hdiagonals, vdiagonals):
    htree = IntervalTree(hdiagonals)
    crossings = []
    for v in vdiagonals:
        for h in htree.at(v.start.point[1]):
            x = h.start.point[0]
            if v[0] <= x <= v[1]:
                crossings.append([h, v])
    return crossings


def find_splitters(hdiagonals, vdiagonals):

    # First find crossings.
    crossings = find_crossings(hdiagonals, vdiagonals)

    # Then tag and convert edge format.
    for i in range(len(hdiagonals)):
        hdiagonals[i].number = i

    for i in range(len(vdiagonals)):
        vdiagonals[i].number = i

    edges = map(lambda c: [c[0].number, c[1].number], crossings)

    # Find independent set.
    # TODO: Replace.
    selected = bipartiteIndependentSet(
        hdiagonals.length,
        vdiagonals.length,
        edges
    )

    # Convert into result format.
    result = []
    ptr = 0
    for i in range(len(selected[0])):
        ptr += 1
        result[ptr] = hdiagonals[selected[0][i]]

    for i in range(len(selected[1])):
        ptr += 1
        result[ptr] = vdiagonals[selected[1][i]]

    # Done.
    return result


def split_segment(segment):

    # Store references.
    a = segment.start
    b = segment.end
    pa = a.prev
    na = a.next
    pb = b.prev
    nb = b.next

    # Fix concavity.
    a.concave = False
    b.concave = False

    # Compute orientation.
    ao = pa.point[segment.direction] == a.point[segment.direction]
    bo = pb.point[segment.direction] == b.point[segment.direction]

    if ao and bo:

        # Case 1:
        #             ^
        #             |
        #   --->A+++++B<---
        #       |
        #       V
        a.prev = pb
        pb.next = a
        b.prev = pa
        pa.next = b
    elif ao and not bo:

        # Case 2:
        #       ^     |
        #       |     V
        #   --->A+++++B--->
        # 
        # 
        a.prev = b
        b.next = a
        pa.next = nb
        nb.prev = pa
    elif not ao and bo:

        # Case 3:
        # 
        # 
        #   <---A+++++B<---
        #       ^     |
        #       |     V
        a.next = b
        b.prev = a
        na.prev = pb
        pb.next = na

    elif not ao and not bo:

        # Case 3:
        #             |
        #             V
        #   <---A+++++B--->
        #       ^
        #       |
        a.next = nb
        nb.prev = a
        b.next = na
        na.prev = b


def find_loops(vertices):

    # Initialize visit flag.
    for v in vertices:
        v.visited = False

    # Walk over vertex list.
    loops = []
    for v in vertices:
        if v.visited:
            continue

        # Walk along loop.
        loop = []
        while not v.visited:
            loop.append(v)
            v.visited = True
            v = v.next
        loops.append(loop)

    return loops


def split_concave(vertices):

    # First step: build segment tree from vertical segments.
    left_segments = []
    right_segments = []
    for v in vertices:
        if v.next.point[1] == v.point[1]:
            if v.next.point[0] < v.point[0]:
                left_segments.append(Segment(v, v.next, 1))
            else:
                right_segments.append(Segment(v, v.next, 1))

    left_tree = IntervalTree(left_segments)
    right_tree = IntervalTree(right_segments)
    for v in vertices:
        if not v.concave:
            continue

        # Compute orientation.
        y = v.point[1]
        if v.prev.point[0] == v.point[0]:
            direction = v.prev.point[1] < y
        else:
            direction = v.next.point[1] < y
        direction = 1 if direction else -1

        # Scan a horizontal ray.
        closest_segment = None
        closest_distance = math.inf * direction
        if direction < 0:
            for h in right_tree.at(v.point[0]):
                x = h.start.point[1]
                if x < y and x > closest_distance:
                    closest_distance = x
                    closest_segment = h
        else:
            for h in left_tree.at(v.point[0]):
                x = h.start.point[1]
                if x > y and x < closest_distance:
                    closest_distance = x
                    closest_segment = h

        # Create two splitting vertices.
        split_a = Vertex([v.point[0], closest_distance], 0, 0, False)
        split_b = Vertex([v.point[0], closest_distance], 0, 0, False)

        # Clear concavity flag.
        v.concave = False

        # Split vertices.
        split_a.prev = closest_segment.start
        closest_segment.start.next = split_a
        split_b.next = closest_segment.end
        closest_segment.end.prev = split_b

        # Update segment tree.
        if direction < 0:
            tree = right_tree
        else:
            tree = left_tree

        tree.remove(closest_segment)

        # TODO: Change to interval.
        tree.add(Segment(closest_segment.start, split_a, 1))
        tree.add(Segment(split_b, closest_segment.end, 1))

        # Append vertices.
        vertices.append(split_a, split_b)

        # Cut v, 2 different cases.
        if v.prev.point[0] == v.point[0]:

            #  Case 1
            #              ^
            #              |
            #  --->*+++++++X
            #      |       |
            #      V       |
            split_a.next = v
            split_b.prev = v.prev
        else:

            #  Case 2
            #      |       ^
            #      V       |
            #  <---*+++++++X
            #              |
            #              |
            split_a.next = v.next
            split_b.prev = v

        # Fix up links.
        split_a.next.prev = split_a
        split_b.prev.next = split_b


def find_regions(vertices):
    for v in vertices:
        v.visited = False

    # Walk over vertex list.
    rectangles = []
    for v in vertices:
        if v.visited:
            continue

        # Walk along loop
        lo = [math.inf, math.inf]
        hi = [-math.inf, -math.inf]
        while not v.visited:
            for j in range(2):
                lo[j] = min(v.point[j], lo[j])
                hi[j] = max(v.point[j], hi[j])
            v.visited = True
            v = v.next
        rectangles.append([lo, hi])
    return rectangles


def decompose_region(paths, clockwise=False):
    if not paths:
        raise Exception('rectangle-decomposition: Must specify list of loops')

    # First step: unpack all vertices into internal format
    vertices = []
    #ptr = 0
    npaths = []
    for i, path in enumerate(paths):
        n = len(path)
        #prev = path[n - 3]
        cur = path[n - 2]
        next = path[n - 1]
        npaths.append([])
        for j in range(n):
            prev = cur
            cur = next
            next = path[j]
            if not isinstance(next, list) or len(next) != 2:
                raise Exception(
                    'rectangle-decomposition: Must specify list of loops')

            #concave = False
            if prev[0] == cur[0]:
                if next[0] == cur[0]:
                    continue

                dir0 = prev[1] < cur[1]
                dir1 = cur[0] < next[0]
                concave = dir0 == dir1
            else:
                if next[1] == cur[1]:
                    continue

                dir0 = prev[0] < cur[0]
                dir1 = cur[1] < next[1]
                concave = dir0 != dir1

            if clockwise:
                concave = not concave

            vtx = Vertex(
                cur,
                i,
                (j + n - 1) % n,
                concave
            )
            npaths[i].append(vtx)
            vertices.append(vtx)

    # Next build interval trees for segments, link vertices into a list
    h_segments = []
    v_segments = []
    for p in npaths:
        for j in range(len(p)):
            a = p[j]
            b = p[(j + 1) % len(p)]
            if a.point[0] == b.point[0]:
                h_segments.append(Segment(a, b, 0))
            else:
                v_segments.append(Segment(a, b, 1))

            if clockwise:
                a.prev = b
                b.next = a
            else:
                a.next = b
                b.prev = a

    h_tree = IntervalTree(h_segments)
    v_tree = IntervalTree(v_segments)

    # Find horizontal and vertical diagonals
    h_diagonals = get_diagonals(vertices, npaths, 0, v_tree)
    v_diagonals = get_diagonals(vertices, npaths, 1, h_tree)

    # Find all splitting edges.
    splitters = find_splitters(h_diagonals, v_diagonals)

    # Cut all the splitting diagonals.
    for splitter in splitters:
        split_segment(splitter)

    # Split all concave vertices.
    split_concave(vertices)

    # Return regions.
    return find_regions(vertices)


if __name__ == '__main__':
    region = [
        [
            [1, 1], [1, 2], [2, 2], [2, 1]
        ],
        [
            [0, 0], [4, 0], [4, 4], [1, 4], [1, 3], [0, 3]
        ]
    ]

    # Next, extract rectangles
    rectangles = decompose_region(region)

    print(rectangles)