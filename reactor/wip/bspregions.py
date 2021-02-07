import random

from reactor.geometry.rect import Rect
from reactor.geometry.vector import Vector2


class BspRegions:

    """
    Taken from: https://arcade.academy/examples/procedural_caves_bsp.html
    """

    def __init__(self, max_, **kwargs):
        super(BspRegions, self).__init__(**kwargs)

        self.max = max_
        #self.max_size = max_size

    def random_split(self, min_row, min_col, max_row, max_col):

        # We want to keep splitting until the sections get down to the threshold
        seg_height = max_row - min_row
        seg_width = max_col - min_col

       # max_ = self.max.run()

        if seg_height < self.max and seg_width < self.max:
            p1 = Vector2(min_row, min_col)
            p2 = Vector2(max_row, max_col)
            self.leaves.append(Rect(p1, p2))
        elif seg_height < self.max <= seg_width:
            self.split_on_vertical(min_row, min_col, max_row, max_col)
        elif seg_height >= self.max > seg_width:
            self.split_on_horizontal(min_row, min_col, max_row, max_col)
        else:
            if random.random() < 0.5:
                self.split_on_horizontal(min_row, min_col, max_row, max_col)
            else:
                self.split_on_vertical(min_row, min_col, max_row, max_col)

    def split_on_horizontal(self, min_row, min_col, max_row, max_col):
        split = (min_row + max_row) // 2 + random.choice((-2, -1, 0, 1, 2))
        self.random_split(min_row, min_col, split, max_col)
        self.random_split(split, min_col, max_row, max_col)

    def split_on_vertical(self, min_row, min_col, max_row, max_col):
        split = (min_col + max_col) // 2 + random.choice((-2, -1, 0, 1, 2))
        self.random_split(min_row, min_col, max_row, split)
        self.random_split(min_row, split, max_row, max_col)

    def run(self, rect):
        self.leaves = []
        self.random_split(rect.p1.x, rect.p1.y, rect.p2.x, rect.p2.y)
        return self.leaves
