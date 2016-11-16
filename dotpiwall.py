#!/usr/bin/env python

'''
Convert PiWall model data into .piwall syntax and v.v.

Def: http://piwall.co.uk/information/16-piwall-configuration-file

Ref: https://github.com/infinnovation/piwall-cvtools/issues/7

TODO: parser
TODO: better system to map pi-tile to tile-id
TODO: system to sort tiles by position of center of ROI and scan order.

18/09/16 20:30 - 21:00 P1 : First draft, simple conversion of model.Wall to .piwall
'''

from model import Tile, RegularWall

utSampleInput_A = '''
'''

utSampleOutput_A = '''
'''

# Uncommenting the following means everyone importing this module gets an unwanted window....
#utWall_A = RegularWall(1920, 1080, 2, 2, 100, 100, 150, 150)

class DotPiwall:
    def __init__(self, name, wall, x = 0, y = 0):
        self.name = name
        self.wall = wall
        self.w = wall.w
        self.h = wall.h
        self.x = x
        self.y = y

    def wall_definition(self):
        s = []
        s.append('[%s_wall]' % self.name)
        s.append('width=%d' % self.w)
        s.append('height=%d' % self.h)
        s.append('x=%d' % self.x)
        s.append('y=%d' % self.y)
        return '\n'.join(s)

    def tile_definition(self, tile):
        s = []
        s.append('[%s_%s]' % (self.name, tile.id))
        s.append('wall=%s' % self.name)
        s.append('width=%d' % tile.W())
        s.append('height=%d' % tile.H())
        s.append('x=%d' % tile.wx)
        s.append('y=%d' % tile.wy)
        return '\n'.join(s)
        
    def __repr__(self):
        s = []
        s.append('%s' % self.wall_definition())
        for tile in self.wall.tilesByOrder:
            s.append('\n%s' % self.tile_definition(tile))
        s.append('\n# config')
        s.append('[%s]' % self.name)
        for i, tile in enumerate(self.wall.tilesByOrder):
            s.append('pi%d=%s_%s' % ( (i + 1) , self.name , tile.id))
        return '\n'.join(s)

def main():
    print(utWall_A.wall)
    tiles = []
    for (tile_position, tile) in utWall_A.tile.iteritems():
        print('%s\n%s' % (tile_position, tile))
        tiles.append(tile)
    dotutwa = DotPiwall('utwall_a', utWall_A.wall)
    print(dotutwa)

if __name__ == '__main__':
    main()

