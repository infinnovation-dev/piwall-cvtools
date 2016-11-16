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
import json
import os
import pickle
import re
import sys

class SimpleWall:
    def __init__(self, w,h):
        self.w = w
        self.h = h
    def __repr__(self):
        return 'I am a %s with dimensions %d x %d' % (self.__class__.__name__, self.w, self.h)

class CompoundWall:
    def __init__(self, w,h):
        self.w = w
        self.h = h
        self.tiles = []
    def add_tile(self, w , h ):
        self.tiles.append(SimpleTile(w,h))
    def __repr__(self):
        s = []
        s.append('I am a %s with dimensions %d x %d' % (self.__class__.__name__, self.w, self.h))
        for t in self.tiles:
            s.append('\tContainer of %s' % t)
        return '\n'.join(s)
    
class SimpleTile:
    def __init__(self, w,h):
        self.w = w
        self.h = h
    def __repr__(self):
        return 'I am a %s with dimensions %d x %d' % (self.__class__.__name__, self.w, self.h)

    
def ut_pickle_simplewall_dump():
    sw1 = SimpleWall(640,480)
    print(sw1)
    with open("sw1.pickle", 'w') as fh:
        pickle.dump(sw1, fh)

def ut_unpickle_simplewall():
    with open("sw1.pickle", 'r') as fh:
        retrieved = pickle.load(fh)
    print(retrieved)

def ut_pickle_compound_wall_dump():
    cw1 = CompoundWall(640,480)
    for h in [100,200,300,400]:
        cw1.add_tile(h, 0.8*h)
    print(cw1)
    with open("cw1.pickle", 'w') as fh:
        pickle.dump(cw1, fh)

def ut_unpickle_compound_wall():
    with open("cw1.pickle", 'r') as fh:
        retrieved = pickle.load(fh)
    print(retrieved)

def ut_json():
    cw1 = CompoundWall(640,480)
    for h in [100,200,300,400]:
        cw1.add_tile(h, 0.8*h)
    cw1_json = json.dumps(cw1)
    cw2 = jdon.loads(cw1_json)
    print('via json')
    print(cw2)
                    

def main():
    ut_pickle_simplewall_dump()
    ut_unpickle_simplewall()
    ut_pickle_compound_wall_dump()
    ut_unpickle_compound_wall()
    ut_json()

if __name__ == '__main__':
    main()
