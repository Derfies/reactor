from reactor.geometry.vector import Vector2


class Rect(object):

    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2

    def __str__(self):
        return '{}, {}'.format(self.p1, self.p2)

    @property
    def width(self):
        return abs(self.p2.x - self.p1.x)

    @property
    def height(self):
        return abs(self.p2.y - self.p1.y)

    @property
    def centre(self):
        return (self.p1 + self.p2) / 2

    def intersects(self, other):
        return (
            self.p1.x < other.p2.x and
            self.p2.x > other.p1.x and
            self.p1.y < other.p2.y and
            self.p2.y > other.p1.y
        )

    def touches(self, other):
        return (
            self.p1.x <= other.p2.x and # If rect1 LHS is less than or equal to rect2 RHS
            self.p2.x >= other.p1.x and
            self.p1.y <= other.p2.y and
            self.p2.y >= other.p1.y
        )

    def normalise(self):
        x1, y1 = self.p1
        x2, y2 = self.p2
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        self.p1 = Vector2(x1, y1)
        self.p2 = Vector2(x2, y2)

    def inflate(self, d):
        self.p1.x -= d
        self.p1.y -= d
        self.p2.x += d
        self.p2.y += d