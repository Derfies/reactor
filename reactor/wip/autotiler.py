import os
import sys
sys.path.append(os.getcwd())

import pyglet


MAP = [
    [0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0],
    [0, 0, 0, 1, 0, 0],
    [0, 0, 1, 1, 0, 0],
    [0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0],
]

MAP = [
    [1, 1, 0],
    [0, 1, 1],
    [0, 1, 0],
]


def fix_bitmask_index(x):
    remainder = x % 4
    base = int(x / 4)
    return (3 - base) * 4 + remainder


def get_bitmask(x, y):

    # Early out if it's just blank space.
    if not MAP[x][y]:
        return 15

    size = 1
    try:
        north_tile = MAP[x][y + size]
    except IndexError:
        north_tile = 0

    try:
        west_tile = MAP[x - size][y]
    except IndexError:
        west_tile = 0

    try:
        east_tile = MAP[x + size][y]
    except IndexError:
        east_tile = 0

    try:
        south_tile = MAP[x][y - size]
    except IndexError:
        south_tile = 0

    mask = north_tile + 2 * west_tile + 4 * east_tile + 8 * south_tile
    print(x, y, ':', north_tile, west_tile, east_tile, south_tile, mask)

    return mask



pyglet.gl.glEnable(pyglet.gl.GL_BLEND)
pyglet.gl.glBlendFunc(
    pyglet.gl.GL_SRC_ALPHA,
    pyglet.gl.GL_ONE_MINUS_SRC_ALPHA
)


window = pyglet.window.Window()

image_path = 'data/Dynamic_Tile_sheet.png'
image = pyglet.image.load(image_path)
sprite = pyglet.sprite.Sprite(image)

explosion_seq = pyglet.image.ImageGrid(image, 4, 4, row_padding=4, column_padding=4)
sprites = []
for i in range(16):
    frame = explosion_seq[i]
    sprites.append(pyglet.sprite.Sprite(frame))



@window.event
def on_draw():
    pyglet.gl.glClearColor(0.5, 0.5, 0.5, 0)
    window.clear()

    sprite.x = 300
    sprite.y = 200
    sprite.draw()

    for x in range(len(MAP)):
        for y in range(len(MAP[x])):
            index = get_bitmask(x, y)

            if index == 15:
                continue

            index = fix_bitmask_index(index)
            sprites[index].x = x * 64
            sprites[index].y = y * 64
            sprites[index].draw()


pyglet.app.run()