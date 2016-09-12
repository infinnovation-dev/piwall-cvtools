#!/usr/bin/env python

#m Initially derived from tilemap.py in the main piwall distribution, instrumented
# modified.

import os
import os.path
from subprocess import Popen, PIPE, call
import time

class Scale:
    def __init__(self, factor, offset):
        self.factor = factor
        self.offset = offset

    def scale(self, value):
        return value * self.factor + self.offset

    def scalev(self, *values):
        return [self.scale(v) for v in values]

    def unscale(self, value):
        return (value - self.offset) / self.factor

    def unscalev(self, *values):
        return [self.unscale(v) for v in values]

    @classmethod
    def from_factor_point(cls, factor, old, new):
        return cls(factor, new - old * factor)

    @classmethod
    def from_points(cls, old0, old1, new0, new1):
        factor = float(new1 - new0) / (old1 - old0)
        return cls(factor, new0 - old0 * factor)

    def __repr__(self):
        return "Scale(offset = %g, factor=%g)" % (self.offset, self.factor)

class Rect:
    def __init__(self, x0, x1, y0, y1):
        self.x0 = x0
        self.x1 = x1
        self.y0 = y0
        self.y1 = y1

    @classmethod
    def from_origin(cls, xsize, ysize):
        return cls(0, xsize, 0, ysize)

    def coords(self):
        return [self.x0, self.x1, self.y0, self.y1]

    def clip(self, limit):
        return Rect(min(max(self.x0,limit.x0),limit.x1),
                    min(max(self.x1,limit.x0),limit.x1),
                    min(max(self.y0,limit.y0),limit.y1),
                    min(max(self.y1,limit.y0),limit.y1))

def iclip(low, high, *values):
    return [int(min(max(low,round(v)),high)) for v in values]

class DebugStream:
    def __init__(self, stream_handle):
        self.stream = stream_handle
    def log(self, message):
        self.stream.writelines(message)

devNull = DebugStream(open("/dev/null", "w"))


# Keep the logging format flexible for db info
sFmt = "%-20s"
gFmt = "%g"
rFmt = "%.1f"
iFmt = "%d"

def tile_map(wall, tile, picture, screen, fit='clip', orient='up', dbstream = devNull):
    picw, pich = map(float, picture)
    wallw, wallh = map(float, wall)
    tilew, tileh, tilex, tiley = map(float, tile)
    screenw, screenh = map(float, screen)

    dbinfo = []
    dbinfo.append("%-20s : w=%g h=%g" % ("picture dimensions", picw, pich))
    dbinfo.append("%-20s : w=%g h=%g" % ("wall dimensions", wallw, wallh))
    dbinfo.append("%-20s : w=%g h=%g x=%g y=%g" % ("tile dimensions", tilew, tileh, tilex, tiley))
    dbinfo.append("%-20s : w=%g h=%g" % ("screen dimensions", screenw, screenh))

    # See how picture will fit on wall - scale factors for wall to picture coords
    xmag = picw / wallw
    ymag = pich / wallh
    dbinfo.append("%-20s : xmag=%g ymag=%g" % ("xmag, ymag (wall to picture factors)", xmag, ymag))

    if fit == 'clip':
        xmag = ymag = min(xmag, ymag)
        dbinfo.append("%-20s : xmag=%g ymag=%g" % ("'clip' a/r preserve min)", xmag, ymag))
    elif fit == 'letterbox':
        xmag = ymag = max(xmag, ymag)
        dbinfo.append("%-20s : xmag=%g ymag=%g" % ("'letterbox' a/r preserve info (max))", xmag, ymag))
    elif fit in ('stretch','squash'):
        # no adjustment
        dbinfo.append("%-20s : ar=%g" % ("stretch/squash new ratio", xmag/ymag))
        pass
    else:
        raise ValueError, 'Unknown fit: %r' % fit

    # Scaling from wall to picture coords
    w2px = Scale.from_factor_point(xmag, wallw/2, picw/2)
    w2py = Scale.from_factor_point(ymag, wallh/2, pich/2)

    dbinfo.append("%-20s : w2px : %s" % ("scale wall to picture X", w2px))
    dbinfo.append("%-20s : w2py : %s " % ("scale wall to picture Y", w2py))

    # Log the original tile geometry.
    dbinfo.append("%-20s : (%g,%g) to (%g,%g))" % ("tile in wall coords", tilex, tiley, tilex+tilew, tiley+tileh))

    # Calculate the rectangle in picture-coordinates we want to display on the tile
    px0, px1 = w2px.scalev(tilex, tilex + tilew)
    py0, py1 = w2py.scalev(tiley, tiley + tileh)

    dbinfo.append("%-20s : (%g,%g) to (%g,%g))" % ("tile in picture coords", px0, py0, px1, py1))

    # Work out crop and region bearing in mind that this rectangle may not lie
    # entirely within the picture

    cx0, cx1 = iclip(0, picw, px0, px1)
    dbinfo.append("%-20s : range %d-%d : bounds %d-%d : clipped %d-%d)" % ("crop X in picture coords", 0, int(picw), int (px0), int(px1), cx0, cx1))

    cy0, cy1 = iclip(0, pich, py0, py1)
    dbinfo.append("%-20s : range %d-%d : bounds %d-%d : clipped %d-%d)" % ("crop Y in picture coords", 0, int(pich), int (py0), int(py1), cy0, cy1))

    crop = '%dx%d+%d+%d' % (cx1-cx0, cy1-cy0, cx0, cy0)
    dbinfo.append("%-20s : %s" % ("crop expression", crop))

    # Wall coordinates of picture
    wx0, wx1 = w2px.unscalev(0, picw)
    wy0, wy1 = w2py.unscalev(0, pich)

    dbinfo.append("%-20s : (%g,%g) to (%g,%g))" % ("picture in wall coords", wx0, wy0, wx1, wy1))

    # Now in screen coordinates
    # tilex -> 0, tilex+tilew -> screenw
    if orient=='up':
        w2sx = Scale.from_points(tilex, tilex + tilew, 0, screenw)
        w2sy = Scale.from_points(tiley, tiley + tileh, 0, screenh)
        sx0, sx1 = w2sx.scalev(wx0, wx1)
        sy0, sy1 = w2sy.scalev(wy0, wy1)
        transform = 0
        dbinfo.append("%-20s : (%g,%g) to (%g,%g))" % ("picture in screen coordinates (o=up)", sx0, sy0, sx1, sy1))
    elif orient=='down':
        w2sx = Scale.from_points(tilex, tilex + tilew, screenw, 0)
        w2sy = Scale.from_points(tiley, tiley + tileh, screenh, 0)
        sx0, sx1 = w2sx.scalev(wx1, wx0)
        sy0, sy1 = w2sy.scalev(wy1, wy0)
        transform = 3
        dbinfo.append("%-20s : (%g,%g) to (%g,%g))" % ("picture in screen coordinates (o=down)", sx0, sy0, sx1, sy1))
    elif orient=='left':
        w2sx = Scale.from_points(tiley, tiley + tileh, screenw, 0)
        w2sy = Scale.from_points(tilex, tilex + tilew, 0, screenh)
        sx0, sx1 = w2sx.scalev(wy1, wy0)
        sy0, sy1 = w2sy.scalev(wx0, wx1)
        transform = 6
        dbinfo.append("%-20s : (%g,%g) to (%g,%g))" % ("picture in screen coordinates (o=left)", sx0, sy0, sx1, sy1))
    elif orient=='right':
        w2sx = Scale.from_points(tiley, tiley + tileh, 0, screenw)
        w2sy = Scale.from_points(tilex, tilex + tilew, screenh, 0)
        sx0, sx1 = w2sx.scalev(wy0, wy1)
        sy0, sy1 = w2sy.scalev(wx1, wx0)
        transform = 5
        dbinfo.append("%-20s : (%g,%g) to (%g,%g))" % ("picture in screen coordinates (o=right)", sx0, sy0, sx1, sy1))
    else:
        raise ValueError, 'Unknown orient: %r' % orient
    dx0, dx1 = iclip(0, screenw, sx0, sx1)
    dbinfo.append("%-20s : range %d-%d : bounds %d-%d : clipped %d-%d)" % ("crop X in screen coords", 0, int(screenw), int (sx0), int(sx1), dx0, dx1))

    dy0, dy1 = iclip(0, screenh, sy0, sy1)
    dbinfo.append("%-20s : range %d-%d : bounds %d-%d : clipped %d-%d)" % ("crop Y in screen coords", 0, int(screenh), int (sy0), int(sy1), dy0, dy1))
    dest = '%dx%d+%d+%d' % (dx1-dx0, dy1-dy0, dx0, dy0)
    dbinfo.append("%-20s : %s" % ("dest expression", dest))

    dbstream.log('\n'.join(dbinfo))
    return crop, dest, transform

if __name__=='__main__':
    import re
    import sys
    import optparse
    rectRE = re.compile(r'(\d+)x(\d+)(?:\+(\d+)\+(\d+))?$')
    def parse_rect(rect):
        m = rectRE.match(rect)
        if not m:
            raise ValueError, 'Invalid rectangle %r' % rect
        return [int(x) if x else 0 for x in m.groups()]

    op = optparse.OptionParser(usage='%prog [-c|-s|-l] wall tile picture screen')
    op.add_option('-c','--clip',
                  action='store_const', dest='fit', const='clip', default='clip',
                  help='Clip edges of picture to cover wall')
    op.add_option('-l','--letterbox',
                  action='store_const', dest='fit', const='letterbox',
                  help='Add black edges to picture to fit within wall')
    op.add_option('-s','--stretch','--squash',
                  action='store_const', dest='fit', const='squash',
                  help='Stretch/squash aspect ratio of picture to fit')
    op.add_option('-o','--orient',
                  type='choice', choices=['up','down','left','right'], default='up',
                  help='Screen orientation')
    opts, args = op.parse_args()
    if len(args) != 4:
        op.error('Wrong number of arguments')
    wall, tile, picture, screen = [parse_rect(a) for a in args]
    print wall, tile, picture, screen
    crop, dest = tile_map2(wall[:2], tile, picture[:2], screen[:2],
                          fit=opts.fit, orient=opts.orient)
    print crop
    print dest
