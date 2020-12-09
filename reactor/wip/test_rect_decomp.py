import unittest

from rect_decomp import decompose_region


class Tests(unittest.TestCase):

    def verify_decomp(self, paths, ccw, expected=None):
        rectangles = decompose_region(paths, ccw)
        if expected is not None:
            self.assertEqual(len(rectangles), expected)

        # Compute area for polygon and check each path is covered by an edgeo of 
        area = 0.0
        for i in range(len(paths)):
            for j in range(len(paths[i])):
                a = paths[i][j]
                b = paths[i][(j + 1) % len(paths[i])]
                if a[1] == b[1]:
                    area += (b[0] - a[0]) * a[1]

        if not ccw:
            area = -area

        # Compute area for boxes.
        boxarea = 0.0
        for r in rectangles:
            self.assertTrue(r[0][0] < r[1][0])
            self.assertTrue(r[0][1] < r[1][1])
            boxarea += (r[1][0] - r[0][0]) * (r[1][1] - r[0][1])

        self.assertEqual(boxarea, area)

    def test_1(self):

        # *-*
        # | |
        # * |
        # | |
        # *-*
        self.verify_decomp([
            [[0, 0], [0, 1], [0, 2], [1, 2], [1, 0]]
        ], True, 1)

    def test_2(self):

        #   *-*
        #   | |
        # *-*-*
        # | |
        # *-*
        self.verify_decomp([
            [[0, 0], [0, 1], [1, 1], [1, 0]],
            [[1, 1], [1, 2], [2, 2], [2, 1]]
        ], True, 2)

    def test_3(self):

        #   *---*
        #   |   |
        # *-*-* |
        # | | | |
        # | *-* |
        # |     |
        # *-----*
        self.verify_decomp([
            [[0, 0], [3, 0], [3, 3], [1, 3], [1, 2], [2, 2], [2, 1], [1, 1],
             [1, 2], [0, 2]]
        ], False, 4)

    def test_4(self):

        #   *-----*
        #   |     |
        # *-*     |
        # |       |
        # | *-*   |
        # | | |   |
        # | *-*   |
        # |       |
        # *-------*
        self.verify_decomp([
            [[1, 1], [1, 2], [2, 2], [2, 1]],
            [[0, 0], [4, 0], [4, 4], [1, 4], [1, 3], [0, 3]]
        ], False, 4)

    def test_plus(self):

        #   *-*
        #   | |
        # *-* *-*
        # |     |
        # *-* *-*
        #   | |
        #   *-*
        plus = [
            [1, 1],
            [0, 1],
            [0, 2],
            [1, 2],
            [1, 3],
            [2, 3],
            [2, 2],
            [3, 2],
            [3, 1],
            [2, 1],
            [2, 0],
            [1, 0]
        ]
        self.verify_decomp([plus], True, 3)

    def test_zigzag(self):

        # *---*
        # |   |
        # *-* *-*
        #   |   |
        #   *---*
        zig_zag = [
            [1, 1],
            [0, 1],
            [0, 2],
            [2, 2],
            [2, 1],
            [3, 1],
            [3, 0],
            [1, 0]
        ]
        self.verify_decomp([zig_zag], True, 2)

    def test_bump(self):

        #    *-*
        #    | |
        #  *-* *-*
        #  |     |
        #  *-----*
        bump = [
            [0, 0],
            [0, 1],
            [1, 1],
            [1, 2],
            [2, 2],
            [2, 1],
            [3, 1],
            [3, 0]
        ]
        self.verify_decomp([bump], True, 2)

    def test_bracket(self):

        #   *-*
        #   | |
        # *-* |
        # |   |
        # *---*
        bracket = [
            [0, 0],
            [0, 1],
            [1, 1],
            [1, 2],
            [2, 2],
            [2, 0]
        ]
        self.verify_decomp([bracket], True, 2)


if __name__ == '__main__':
      unittest.main()
