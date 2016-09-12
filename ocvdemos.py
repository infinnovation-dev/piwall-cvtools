#!/usr/bin/env python

'''
OpenCV demos.
'''

from itertools import count
import glob
import os
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
from common import clock

# Record the results of processing the video using vwriter
from vwriter import VideoWriter
from piwall import ImageViewer
from frame import Frame


class Image:
    def __init__(self, path):
        self.img = cv2.imread(path)
        h,w,c = self.img.shape
        print('%s : h %d w %d c %d' % (path, h, w, c))

def main():
    bigRodent = Image('data/poster_rodents_big.jpg')
    
if __name__ == '__main__':
    main()
