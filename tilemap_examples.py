#!/usr/bin/env python

'''
Wall geometry examples combining the piwall tilemap algorithms with some OpenCV to generate practical examples.
'''

import pdb
import sys
from model import Tile
sys.path.append('..')
from tilemap import tile_map, DebugStream


# Todo: make this a Singleton somehow.
samsung206bw = Tile( 434, 270, 20, 35, 20, 20, units = 'mm', name = 'Samsung 206BW',)

def SamsungRibbon2_1(picture, screen, fit='clip', orient='up'):
    monitor1=samsung206bw
    monitor2=samsung206bw
    wallw = monitor1.W() + monitor2.W()
    wallh = monitor1.H()
    wall = [wallw, wallh]
    t1w = t2w = monitor1.w
    t1h = t2h = monitor1.h
    t1x = monitor1.l
    t1y = monitor1.t
    t2x = t1x + t1w
    t2y = t1y
    tile1 = [t1w, t1h, t1x, t1y]
    tile2 = [t2w, t2h, t2x, t2y]
    t1fh = open("tile1_transformations_log_%s_%s.txt" % (fit,orient), "w")
    t1crop, t1dest, t1trans = tile_map(wall, tile1, picture, screen, fit, orient, dbstream = DebugStream(t1fh))
    print(t1crop,t1dest)
    t1fh.close()
    t2fh = open("tile2_transformations_log_%s_%s.txt" % (fit,orient), "w")
    t2crop, t2dest, t2trans = tile_map(wall, tile2, picture, screen, fit, orient, dbstream = DebugStream(t2fh))    
    print(t2crop,t2dest)
    t2fh.close()

def SamsungSquare2x2(picture, screen, fit='letterbox', orient='up'):
    monitor1=samsung206bw
    monitor2=samsung206bw
    monitor3=samsung206bw
    monitor4=samsung206bw
    wallw = 2*monitor1.W()
    wallh = 2*monitor1.H()
    wall = [wallw, wallh]
    t1w = t2w = t3w = t4w = monitor1.w
    t1h = t2h = t3h = t4h = monitor1.h
    #
    t1x = monitor1.l
    t1y = monitor1.t
    #
    t2x = t1x + t1w
    t2y = t1y
    #
    t3x = t1x
    t3y = t1y+t1h
    # 
    t4x = t1x+t1w
    t4y = t1y+t1h
    #
    tile1 = [t1w, t1h, t1x, t1y]
    tile2 = [t2w, t2h, t2x, t2y]
    tile3 = [t3w, t3h, t3x, t3y]
    tile4 = [t3w, t3h, t4x, t4y]
    i=1
    for tile in [tile1, tile2, tile3, tile4]:
        fh = open("tile%d_transformations_log_%s_%s.txt" % (i, fit,orient), "w")
        crop, dest, trans = tile_map(wall, tile, picture, screen, fit, orient, dbstream = DebugStream(fh))
        print(crop,dest)
        fh.close()
        i+=1

def main():
    hd_picture = [1920,1080]
    monitor=samsung206bw
    screenw = 1680
    screenh = 1050
    screen = [screenw, screenh]
    #    SamsungRibbon2_1(hd_picture, screen, fit='clip', orient='up')
    SamsungSquare2x2(hd_picture, screen, fit='clip', orient='up')
    SamsungSquare2x2(hd_picture, screen, fit='letterbox', orient='up')
    SamsungSquare2x2(hd_picture, screen, fit='letterbox', orient='down')
    SamsungSquare2x2(hd_picture, screen, fit='letterbox', orient='left')
    SamsungSquare2x2(hd_picture, screen, fit='letterbox', orient='right')
    pass
    sys.exit(0)

if __name__=='__main__':
    main()
    # To refactor later
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
