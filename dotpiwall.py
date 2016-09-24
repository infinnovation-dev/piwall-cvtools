#!/usr/bin/env python

'''
Convert PiWall model data into .piwall syntax and v.v.

Def: http://piwall.co.uk/information/16-piwall-configuration-file

Ref: https://github.com/infinnovation/piwall-cvtools/issues/7

TODO: better system to map pi-tile to tile-id

24/09/16 15:15 - 15:30 .piwall is generated from the top left to the bottom right
20/09/16 00:30 - 01:40 Piwall parser implemented
18/09/16 20:30 - 21:00 P1 : First draft, simple conversion of model.Wall to .piwall
'''

from model import Tile, RegularWall, Wall

utSampleInput_A = '''
'''

utSampleOutput_A = '''
'''

utWall_A = RegularWall(1920, 1080, 2, 2, 100, 100, 150, 150)

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
        s.append('wall=%s_wall' % self.name)
        s.append('width=%d' % tile.W())
        s.append('height=%d' % tile.H())
        s.append('x=%d' % tile.wx)
        s.append('y=%d' % tile.wy)
        return '\n'.join(s)

    @staticmethod
    def parser(file_location):
        definitions = {}
        walls_dictionary = {}
        last_definition = ''
        # Read config
        with open(file_location) as fp:
            for line in fp:
                trimmed_line = line.replace('\n', '').replace(' ', '')
                if line[0] != '#' and len(trimmed_line) > 0:
                    if line[0] == '[':
                        last_definition = (trimmed_line.replace('[','').replace(']',''))
                        definitions[last_definition] = {}
                    else:
                        attributes = trimmed_line.split('=')
                        definitions[last_definition][attributes[0]] = attributes[1]
        #print(definitions)

        # Parse objects
        for key, value in definitions.iteritems():
            #print('value = key = {}'.format(value, key))

            if 'wall' in value.keys():
                #print('This is a tile : {}'.format(key))
                newTile = Tile(int(value['width']), int(value['height']), 0, 0, 0, 0,
                               key.split('_')[1], key.split('_')[0])
                if value['wall'].split('_')[0] in walls_dictionary.keys():
                    if 'tiles' not in walls_dictionary[value['wall'].split('_')[0]].keys():
                        walls_dictionary[value['wall'].split('_')[0]]['tiles'] = []
                    walls_dictionary[value['wall'].split('_')[0]]['tiles'].append(newTile)
                else:
                    walls_dictionary[value['wall'].split('_')[0]] = {}
                    walls_dictionary[value['wall'].split('_')[0]]['tiles'] = []
                    walls_dictionary[value['wall'].split('_')[0]]['tiles'].append(newTile)

            elif 'width' in value.keys():
                #print('This is a wall : {}'. format(key))
                if key.split('_')[0] not in walls_dictionary.keys():
                    walls_dictionary[key.split('_')[0]] = {}

                newWall = Wall(int(value['width']), int(value['height']), int(value['x']), int(value['y']))
                walls_dictionary[key.split('_')[0]]['definition'] = newWall

            else:
                print('This is the config : {}'.format(key))

        result = []
        for key, value in walls_dictionary.iteritems():
            print(len(value['tiles']))
            for tile in value['tiles']:
                value['definition'].add_tile(tile, int(definitions['{}_{}'.format(tile.name,tile.id)]['x']),
                                             int(definitions['{}_{}'.format(tile.name,tile.id)]['x']))
            result.append(value['definition'])
        return result

        
    def __repr__(self):
        s = []
        s.append('%s' % self.wall_definition())
        tiles = sorted(self.wall.tilesByOrder, key=lambda tile:tile.wx) # sort on x (secondary)
        sortedTiles = sorted(tiles, key=lambda tile: tile.wy)  # sort on y (primary)
        for tile in sortedTiles:
            s.append('\n%s' % self.tile_definition(tile))
        s.append('\n# config')
        s.append('[%s]' % self.name)
        for i, tile in enumerate(sortedTiles):
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
    #test = DotPiwall.parser("generatedpiwall")
    #print("config has {} wall configuration".format(len(test)))
    #test[0].show()

if __name__ == '__main__':
    main()

