import os
import sys
import random
random.seed(2)
sys.path.append(os.getcwd())

import pyglet

from reactor import utils
from reactor.geometry.rect import Rect
from reactor.geometry.vector import Vector2
from reactor.mapgenerator import MapGenerator


GRID_PATH = 'data/tree1.gexf'
TILE_PATH = 'data/grass.png'
TILE_SIZE = Vector2(16, 16)
MAP_WIDTH = 60
MAP_HEIGHT = 60
ROW_GUTTER = 0#4
COL_GUTTER = 0#4
WINDOW_WIDTH = 500
WINDOW_HEIGHT = 500


def get_rects(map_):
    rects = []

    min_x = 0
    min_y = 0

    for room in map_.rooms:
        rects.append(room)
        min_x = min(min_x, room.p1.x)
        min_y = min(min_y, room.p1.y)

    # Test drawing thick edges.
    for edge in map_.layout.edges:
        rect = Rect(*utils.get_edge_positions(map_.layout, edge))
        rect.normalise()
        rect.inflate(0.5)
        rects.append(rect)

        min_x = min(min_x, rect.p1.x)
        min_y = min(min_y, rect.p1.y)

    print('min_x:', min_x)
    print('min_y:', min_y)

    # Offset all rects.
    for rect in rects:
        rect.p1.x -= min_x + 0
        rect.p2.x -= min_x + 0
        rect.p1.y -= min_y + 0
        rect.p2.y -= min_y + 0

        print('after:', rect)

    for rect in rects:
        rect.p1.x += 1
        rect.p2.x += 1
        rect.p1.y += 1
        rect.p2.y += 1

    return rects


def build_map(width, height, rects):
    map_ = []
    for x in range(width):
        row = []
        for y in range(height):
            point = Vector2(x + 0.5, y + 0.5)
            point_within = False
            for r in rects:
                point_within = point_within or r.contains_point(point)
                if point_within:
                    break
            row.append(point_within)
        map_.append(row)
    return map_


def fix_bitmask_index(x):
    """
    Inverts the row index as pyglet inverted this from source code.

    """
    remainder = x % 4
    base = int(x / 4)
    return (3 - base) * 4 + remainder


def get_bitmask(x, y, map_):

    # Early out if it's just blank space.
    if not map_[x][y]:
        return 15

    size = 1
    try:
        north_tile = map_[x][y + size]
    except IndexError:
        north_tile = 0

    try:
        west_tile = map_[x - size][y]
    except IndexError:
        west_tile = 0

    try:
        east_tile = map_[x + size][y]
    except IndexError:
        east_tile = 0

    try:
        south_tile = map_[x][y - size]
    except IndexError:
        south_tile = 0

    mask = north_tile + 2 * west_tile + 4 * east_tile + 8 * south_tile

    return mask



pyglet.gl.glEnable(pyglet.gl.GL_BLEND)
pyglet.gl.glBlendFunc(
    pyglet.gl.GL_SRC_ALPHA,
    pyglet.gl.GL_ONE_MINUS_SRC_ALPHA
)
pyglet.gl.glTexParameteri(pyglet.gl.GL_TEXTURE_2D, pyglet.gl.GL_TEXTURE_MAG_FILTER, pyglet.gl.GL_NEAREST)


window = pyglet.window.Window(width=WINDOW_WIDTH, height=WINDOW_HEIGHT)


image = pyglet.image.load(TILE_PATH)
sprite = pyglet.sprite.Sprite(image)

explosion_seq = pyglet.image.ImageGrid(image, 4, 4, row_padding=ROW_GUTTER, column_padding=COL_GUTTER)
sprites = []
for i in range(16):
    frame = explosion_seq[i]
    sprite = pyglet.sprite.Sprite(frame)
    sprites.append(sprite)
    sprite.scale_x = TILE_SIZE.x / sprite.width
    sprite.scale_y = TILE_SIZE.y / sprite.height


gen = MapGenerator(GRID_PATH)
map1 = gen.run()



map_ = build_map(MAP_WIDTH, MAP_HEIGHT, get_rects(map1))


@window.event
def on_draw():
    pyglet.gl.glClearColor(0.5, 0.5, 0.5, 0)
    window.clear()

    # sprite.x = 300
    # sprite.y = 200
    # sprite.draw()

    for x in range(len(map_)):
        for y in range(len(map_[x])):
            index = get_bitmask(x, y, map_)
            index = fix_bitmask_index(index)
            sprites[index].x = x * TILE_SIZE.x
            sprites[index].y = y * TILE_SIZE.y
            sprites[index].draw()


#utils.draw_map(map1)
pyglet.app.run()