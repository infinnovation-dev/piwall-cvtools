#!/usr/bin/env python

'''
Model problems : generate some idealised images to test basic algorithm.

Then refine when various issues are added (noise, transformation, ...)

Also demonstrates the use of openCV drawing and transformation functions.
'''

# 
# More feature ideas : need to be able to generate geometry files (or close to the syntax thereof and vice-versa).

### Next iteration
# Add option to render tile pixels in solid colour
# Add tile capability to hold an internal image
# Add option to render tile pixels as a masked copy of that image (simulating the piwall geometry concept !)
#  NB : Do we mask and scale up, or scale up, then mask ?
#
# Deal with rounding errors

from itertools import count
import glob
import os
import re
import sys

# Python 2/3 compatibility
PY3 = sys.version_info[0] == 3

if PY3:
    xrange = range

import numpy as np
from matplotlib import pyplot as plt
import cv2
import pdb
import time

sys.path.append('/home/adam/pd/opencv/opencv-3.1.0/samples/python/')
from video import create_capture, Album
from time import clock

# Record the results of processing the video using vwriter
from vwriter import VideoWriter
from piwall import ImageViewer
from frame import Frame

sys.path.append('..')
from tilemap import tile_map, DebugStream


###
### Utility functions.
###

###
### Next Refactor Target : pull out common rectangular geometry in general.
###

class Anchor():
    '''Allow shapes to be positioned w.r.t a key point.'''

    def __init__(self, label):
        self.label = label


###
### How to work with Points (x,y) and Vectors [(x,y), (a,b)] in openCV ?
###   or numpy, or some general 2D graphics libraries....

def add2D(a, b):
    return tuple(map(sum, zip(a, b)))


class Vector:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, vector):
        return Vector(self.x + vector.x, self.y + vector.y)

    def translate(self, displacement):
        '''Syntactic sugar'''
        self.x = self.x + displacement.x
        self.y = self.y + displacement.y

    def coords(self):
        '''Return as tuple convenient for use in cv2'''
        return (self.x, self.y)

    def __repr__(self):
        return '(%f,%f)' % (self.x, self.y)


class Rectangle:
    # Convenient for cv2.rectangle
    def __init__(self, tl, br):
        self.tl = tl
        self.br = br

    def translate(self, displacement):
        self.tl = self.tl.translate(displacement)
        self.br = self.br.translate(displacement)


class Color:
    def __init__(self, b, g, r, desc=None):
        self.bgr = (b, g, r)
        self.desc = desc


RED = Color(0, 0, 255)
BLUE = Color(255, 0, 0)
GREEN = Color(0, 255, 0)


###
### Working Model.
###

class Resolution:
    def __init__(self, x, y, name=''):
        self.x = x
        self.y = y
        self.name = name


HDres = Resolution(1920, 1080, 'FullHD')

rectRE = re.compile(r'(\d+)x(\d+)(?:\+(\d+)\+(\d+))?$')


def parse_rect(rect):
    m = rectRE.match(rect)
    if not m:
        raise ValueError, 'Invalid rectangle %r' % rect
    return [int(x) if x else 0 for x in m.groups()]


class Crop:
    def __init__(self, expr):
        self.expr = expr
        self.values = parse_rect(self.expr)
        (self.w, self.h, self.x, self.y) = self.values

    def __repr__(self):
        return '%s : w=%d h=%d x=%d y=%d' % (self.expr, self.w, self.h, self.x, self.y)


class Projection:
    '''A projection associates a video resolution with a wall to permit calculation of transformations between coordinate spaces.'''

    def __init__(self, resolution, wall):
        self.resolution = resolution
        self.wall = wall
        self.tileROIs = []

    def run_transforms(self):
        pic_tuple = [self.resolution.x, self.resolution.y]
        wall_tuple = [self.wall.w, self.wall.h]
        screen_tuple = [1680, 1050]
        for tile in self.wall.tilesByOrder:
            tile_tuple = [tile.w, tile.h, tile.wx, tile.wy]
            crop, dest, trans = tile_map(wall_tuple, tile_tuple, pic_tuple, screen_tuple)
            print(crop, dest)
            self.tileROIs.append(Crop(crop))
            print(self.tileROIs[-1])

    def render(self, img, color=RED, thickness=3, fname=None):
        self.img = img
        for c in self.tileROIs:
            tl = (c.x, c.y)
            br = (c.x + c.w, c.y + c.h)
            cv2.rectangle(self.img, tl, br, color.bgr, thickness)
        vw = ImageViewer(self.img)
        # TODO: refactor using with
        if fname:
            fh = open(fname, 'w')
            cv2.imwrite(fname, self.img)
            fh.close()
        vw.windowShow()


class Wall:
    '''A wall is a container of tiles, which are display regions.  A tile may have a bezel, or non-display border around it.'''

    def __init__(self, w, h, tiles=None, desc=''):
        self.w = w
        self.h = h
        self.desc = desc
        self.tilesByOrder = []
        self.tilesByName = {}
        self.tilesById = {}
        self.tilesByPixelOffset = {}
        self.img = None
        self.reset()

    def resize(self, w):
        print('Wall resized to w %d' % w)
        self.reset(w=w)

    def reset(self, w=0, h=0, force=False):
        self.img = np.zeros((self.h, self.w, 3), np.uint8)

    def add_tile(self, tile, x, y):
        '''Add a tile at position x,y.'''
        tile.addToWall(self, x, y)
        self.tilesByOrder.append(tile)
        self.tilesByName[tile.name] = tile
        self.tilesById[tile.id] = tile
        self.tilesByPixelOffset[(x, y)] = tile
        print('Wall added : %s' % tile.name)
        print(tile)

    # TODO: Decorator to add .tiles as .tilesByOrder()

    def add_bg(self, img):
        '''Add a background for the wall taken from a still image.   Image will need to be scaled to wall geometry.'''
        pass

    def render(self, w=0, h=0, bezelColor=RED, bezelThickness=3, pixelColor=BLUE, pixelThickness=3):
        self.reset(force=True)
        for tile in self.tilesByOrder:
            (tl, br) = tile.bb(bezel=True, wallCoords=True)
            cv2.rectangle(self.img, tl, br, bezelColor.bgr, bezelThickness)
            (tl, br) = tile.bb(pixel=True, wallCoords=True)
            cv2.rectangle(self.img, tl, br, pixelColor.bgr, pixelThickness)

    def show(self):
        self.render()
        vw = ImageViewer(self.img)
        vw.windowShow()

    def __repr__(self):
        s = []
        s.append('Wall with w = %d, h = %d, shape is %s' % (self.w, self.h, self.img.shape))
        return '\n'.join(s)

    def draw(self, image):
        for tile in self.tilesByOrder:
            cv2.putText(image, "ID #{}".format(tile.id), (tile.wx, tile.wy),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)
            cv2.rectangle(image, (tile.wx, tile.wy), (tile.wx + tile.W(), tile.wy + tile.H()),
                          (0, 255, 0), 2)
            cv2.imshow("image", image)


class Tile:
    ''' 
    A tile is a display area of dimension
    w : width 
    h : height    
    It may have a non-display border area or bezel with dimensions
    t : top
    b : botton
    l : left
    r : right
    #
    CV2 rectangle coordinates go from (0,0) at top left, to (w,h) at bottom right
    #
    It can be pinned to a wall by the top left corner (of full outer bounding box including bezel) at wall coordinates wx, wy.
    '''
    _ids = count(0)

    def __init__(self, w, h, t=0, b=0, l=0, r=0, id=None, name=None):
        self.w = w
        self.h = h
        self.t = t
        self.b = b
        self.l = l
        self.r = r
        if not id:
            self.id = self._ids.next()
        else:
            self.id = id
        if not name:
            self.name = "Tile %d" % self.id
        else:
            self.name = name
        # If partipating in a wall, additional metadata.
        self.wall = None
        self.orderInWall = -1
        self.wx = None
        self.wy = None

    def copy(self):
        newTile = Tile(self.w, self.h, self.t, self.b, self.l, self.r, self.id, self.name)
        newTile.wall = self.wall
        newTile.orderInWall = self.orderInWall
        newTile.wx = self.wx
        newTile.wy = self.wy
        return newTile

    def addToWall(self, wall, x, y):
        self.wall = wall
        self.orderInWall = len(wall.tilesByOrder) + 1
        self.wx = x
        self.wy = y

    def W(self):
        return (self.l + self.w + self.r)

    def H(self):
        return (self.t + self.h + self.b)

    def bb(self, bezel=False, pixel=True, wallCoords=False):
        if bezel:
            (tl, br) = self._bb_bezel()
        else:
            (tl, br) = self._bb_pixel()
        if wallCoords:
            t = Vector(self.wx, self.wy)
            tl.translate(t)
            br.translate(t)
        return (tl.coords(), br.coords())

    def containsCoordinate(self, point):
        if point[0] >= self.wx and point[0] <= (self.wx + self.W()) and point[1] >= self.wy and point[1] <= self.wy + self.H():
            return True
        return False

    def _bb_bezel(self):
        tl = Vector(0, 0)
        br = tl + Vector(self.W(), self.H())
        return (tl, br)

    def _bb_pixel(self):
        tl = Vector(self.l, self.t)
        br = tl + Vector(self.w, self.h)
        return (tl, br)

    def __repr__(self):
        (bztl, bzbr) = self.bb(bezel=True)
        (pxtl, pxbr) = self.bb(pixel=True)
        if self.wall:
            wallInfo = 'Part of wall %s at location (%f,%f)' % (self.wall.desc, self.wx, self.wy)
        else:
            wallInfo = 'Not part of any wall'
        fmt = '''%s : bb [%s , %s] : pixels [%s , %s].  %s'''
        return fmt % (self.name, bztl, bzbr, pxtl, pxbr, wallInfo)


###
### Specific use of the model classes
###

class RegularWall:
    '''Geometry handler for regular tiles, simple spacing.  Prototyping a general Wall Interface and features.'''

    def __init__(self, w, h, r, c, dx, dy, DX=0, DY=0):
        # Tiles of size w x h arranged in r rows, c columns : N of tiles = r * c
        self.w = w
        self.h = h
        self.r = r
        self.c = c
        self.N = r * c
        # Parse horizontal padding dx between tiles, DX to edge of wall at extrema
        self.dx = dx
        if DX == 0:
            self.DX = dx
        else:
            self.DX = DX
        # Parse vertical padding dy between tiles, DY to edge of wall at extrema
        self.dy = dy
        if DY == 0:
            self.DY = dy
        else:
            self.DY = DY
        # Overall wall geometry
        m = Tile(w, h)
        self.W = (r * m.W()) + ((r - 1) * self.dx) + (2 * self.DX)
        self.H = (c * m.H()) + ((c - 1) * self.dy) + (2 * self.DY)
        self.wall = Wall(self.W, self.H)
        # Offsets and Objects modelling the tiles, keyed by position (r,c)
        self.offsets = {}
        self.tile = {}
        for row in range(0, r):
            for col in range(0, c):
                key = (row + 1, col + 1)
                m = Tile(w, h)
                x = self.DX + (row * self.dx) + (row * m.W())
                y = self.DY + (col * self.dy) + (col * m.H())
                self.wall.add_tile(m, x, y)
                self.tile[key] = m
        print(self.wall)
        self.wall.show()


def main():
    rw = RegularWall(1920, 1080, 2, 2, 100, 100, 150, 150)
    pgui = ProjectionGUI(HDres, rw.wall)
    print("finished")
    sys.exit(0)
    p1 = Projection(HDres, rw.wall)
    p1.run_transforms()
    beach = cv2.imread('data/antigua_beaches-wallpaper-1920x1080.jpg')
    p1.render(beach, fname='data/beach-2x2-hd.png')
    rw = RegularWall(1920, 1080, 4, 7, 100, 100, 150, 150)
    p1 = Projection(HDres, rw.wall)
    p1.run_transforms()
    beach = cv2.imread('data/antigua_beaches-wallpaper-1920x1080.jpg')
    p1.render(beach, fname='data/beach-4x7-hd.png')


class ProjectionGUI(object):
    window_name = "Infinnovation Projection GUI"

    def __init__(self, resolution, wall):
        cv2.namedWindow(self.window_name)
        cv2.imshow(self.window_name, wall.img)
        cv2.createTrackbar("wall width", self.window_name, wall.w, 1000, wall.resize)
        cv2.waitKey()


if __name__ == '__main__':
    main()
