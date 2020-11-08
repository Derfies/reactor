import os
import sys
import random
random.seed(0)
sys.path.append(os.getcwd())

import pygame as pg

from reactor import utils
from reactor.geometry.vector import Vector2
from reactor.mapgenerator import MapGenerator


GRID_PATH = 'data/reactor5.gexf'
MAP_WIDTH = 60
MAP_HEIGHT = 60
WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 1400
TILESIZE_W = 32
TILESIZE_H = 32
BLUE = (72, 215, 216) # sea blue for the background
# bitmask-to-base10 values and the corresponding tile index
TILE_MAP = {
    2 : 1,
    8 : 2, 
    10 : 3, 
    11 : 4, 
    16 : 5, 
    18 : 6, 
    22 : 7, 
    24 : 8,
    26 : 9, 
    27 : 10, 
    30 : 11, 
    31 : 12, 
    64 : 13,
    66 : 14, 
    72 : 15, 
    74 : 16, 
    75 : 17, 
    80 : 18, 
    82 : 19, 
    86 : 20, 
    88 : 21, 
    90 : 22, 
    91 : 23, 
    94 : 24, 
    95 : 25, 
    104 : 26, 
    106 : 27, 
    107 : 28, 
    120 : 29, 
    122 : 30, 
    123 : 31, 
    126 : 32, 
    127 : 33, 
    208 : 34, 
    210 : 35, 
    214 : 36, 
    216 : 37, 
    218 : 38, 
    219 : 39, 
    222 : 40, 
    223 : 41, 
    248 : 42,
    250 : 43, 
    251 : 44, 
    254 : 45, 
    255 : 46, 
    0 : 47
}
SAMPLE_OFFSET = Vector2(0.5, 0.5)


class TileMap:

    def __init__(self):
        gen = MapGenerator(GRID_PATH)
        self.map = gen.run()
        self.min_x = 0
        self.min_y = 0
        self.room_rects = self.get_room_rects()
        self.edge_rects = self.get_edge_rects()
        self.rects = self.room_rects + self.edge_rects
        self.offset_rects(self.rects)

    def get_edge_rects(self):
        rects = []
        for edge in self.map.layout.edges:
            rect = utils.get_edge_rect(self.map.layout, edge)
            rects.append(rect)
            self.min_x = min(self.min_x, rect.p1.x)
            self.min_y = min(self.min_y, rect.p1.y)

        return rects

    def get_room_rects(self):
        rects = []
        for room in self.map.rooms:
            rects.append(room)
            self.min_x = min(self.min_x, room.p1.x)
            self.min_y = min(self.min_y, room.p1.y)
        return rects

    def offset_rects(self, rects):

        # Offset all rects.
        for rect in rects:
            rect.p1.x -= self.min_x + 0
            rect.p2.x -= self.min_x + 0
            rect.p1.y -= self.min_y + 0
            rect.p2.y -= self.min_y + 0

        # Move away from the edge of the draw area.
        for rect in rects:
            rect.p1.x += 1
            rect.p2.x += 1
            rect.p1.y += 1
            rect.p2.y += 1

    def get_intersecting_rooms(self, y, x):
        p = Vector2(x, y) + SAMPLE_OFFSET
        return {
            r
            for r in self.room_rects
            if r.contains_point(p)
        }

    def get_intersecting_edges(self, y, x):
        p = Vector2(x, y) + SAMPLE_OFFSET
        return {
            r
            for r in self.edge_rects
            if r.contains_point(p)
        }

    def test_point(self, y, x):
        p = Vector2(x, y) + SAMPLE_OFFSET
        for r in self.rects:
            if r.contains_point(p):
                return True
        return False

    def test_point2(self, y, x, other_edge_rects, room_rects):
        has_rooms = len(room_rects) > 0
        rooms_same = self.get_intersecting_rooms(y, x) == room_rects
        edge_rects = self.get_intersecting_edges(y, x)
        #edges_same = edge_rects == other_edge_rects
        return has_rooms and rooms_same or edge_rects & other_edge_rects#rooms_same and edges_same
        # if rooms_same:
        #     return True
        # else:
        #     return rooms_same and edges_same


def add_bin(a, b):
    # adds two binary strings together
    return bin(int(a, 2) + int(b, 2))


def bool_list_to_mask(bools):
    mask_string = ''.join(['{:d}'.format(b) for b in bools])
    return int(mask_string, 2)


class Game:
    
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        #self.screen = pg.display.set_mode((0, 0), pg.FULLSCREEN)
        self.clock = pg.time.Clock()
        self.show_grid = False
        
        # load tileset
        self.tileset_image = pg.image.load('data/autotiles.png').convert()
        tiles_w = int(self.tileset_image.get_width() / TILESIZE_W)
        tiles_h = int(self.tileset_image.get_height() / TILESIZE_H)

        # load tiles as subsurfaces from a tileset image
        self.tileset = []
        for i in range(tiles_w * tiles_h):
            r = (i % tiles_w * TILESIZE_W, int(i / tiles_w) * TILESIZE_H,
                 TILESIZE_W, TILESIZE_H)
            self.tileset.append(self.tileset_image.subsurface(r))
        
    def construct_map(self):

        # Create an empty surface for the map.
        self.map_image = pg.Surface((
            MAP_WIDTH * TILESIZE_W,
            MAP_HEIGHT * TILESIZE_H
        ))
        self.map_image.fill(BLUE)
        
        # Loop through the map data array and blit the corresponding tile.
        tile_map = TileMap()
        for y in range(MAP_WIDTH):
            for x in range(MAP_HEIGHT):

                # x and y are flipped because I loop through the vertical
                # component (columns) first
                if tile_map.test_point(y, x):

                    # calculate the bitmask if the tile is 1 (land)
                    bitmask = [False] * 8

                    edge_rects = tile_map.get_intersecting_edges(y, x)
                    room_rects = tile_map.get_intersecting_rooms(y, x)
                    
                    # loop over all neighbor tiles
                    if tile_map.test_point2(y - 1, x - 1, edge_rects, room_rects):
                        # check adjacent tiles to the west and south
                        # this is done to reduce the possible index values to 48 in total
                        if tile_map.test_point2(y - 1, x, edge_rects, room_rects) and tile_map.test_point2(y, x - 1, edge_rects, room_rects):
                            bitmask[7] = True

                    if tile_map.test_point2(y - 1, x, edge_rects, room_rects):
                        bitmask[6] = True

                    if tile_map.test_point2(y - 1, x + 1, edge_rects, room_rects):
                        if tile_map.test_point2(y - 1, x, edge_rects, room_rects) and tile_map.test_point2(y, x + 1, edge_rects, room_rects):
                            bitmask[5] = True

                    if tile_map.test_point2(y, x - 1, edge_rects, room_rects):
                            bitmask[4] = True

                    if tile_map.test_point2(y, x + 1, edge_rects, room_rects):
                        bitmask[3] = True

                    if tile_map.test_point2(y + 1, x - 1, edge_rects, room_rects):
                        if tile_map.test_point2(y + 1, x, edge_rects, room_rects) and tile_map.test_point2(y, x - 1, edge_rects, room_rects):
                            bitmask[2] = True

                    if tile_map.test_point2(y + 1, x, edge_rects, room_rects):
                        bitmask[1] = True

                    if tile_map.test_point2(y + 1, x + 1, edge_rects, room_rects):
                        if tile_map.test_point2(y + 1, x, edge_rects, room_rects) and tile_map.test_point2(y, x + 1, edge_rects, room_rects):
                            bitmask[0] = True
                        
                    key = bool_list_to_mask(bitmask)
                    try:
                        self.map_image.blit(
                            self.tileset[TILE_MAP[key]],
                            (x * TILESIZE_W, y * TILESIZE_H)
                        )
                    except KeyError:
                        # fail safe in case the calculated bitmask is wrong
                        # this is only for bugfixing
                        print('tile not found for {:08b}'.format(key))
                        s = pg.Surface((32, 32))
                        s.fill(pg.Color('red'))
                        self.map_image.blit(s, (x * TILESIZE_W, y * TILESIZE_H))
                        
    def update(self):

        if self.mouse_pressed[0]:
            # left mouse pressed
            self.construct_map()
    
    def draw(self):
        self.screen.fill(pg.Color('black'))
        self.screen.blit(self.map_image, (0, 0))
        
        tiles_w = self.screen.get_width() // TILESIZE_W
        tiles_h = self.screen.get_height() // TILESIZE_H
        
        if self.show_grid:
            color = pg.Color('white')
            for i in range(tiles_w):
                start = (i * TILESIZE_W, 0)
                end = (i * TILESIZE_W, self.screen.get_height())
                pg.draw.line(self.screen, color, start, end)
            for i in range(tiles_h):
                start = (0, i * TILESIZE_H)
                end = (self.screen.get_width(), i * TILESIZE_H)
                pg.draw.line(self.screen, color, start, end)
        
        pg.display.update()
        
    def run(self):
        self.construct_map()
        
        self.running = True
        while self.running:
            # reset mouse buttons
            self.mouse_pressed = [0, 0, 0, 0, 0]
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.running = False
                elif event.type == pg.MOUSEBUTTONDOWN:
                    self.mouse_pressed[event.button - 1] = 1
                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_g:
                        self.show_grid = not self.show_grid
                    # else:
                    #     self.running = False
                    
            self.clock.tick(30)
            
            self.update()
            self.draw()
        
        pg.quit()
        

if __name__ == '__main__':
    g = Game()
    g.run()
    pg.quit()

