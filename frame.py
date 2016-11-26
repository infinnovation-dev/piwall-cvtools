#!/usr/bin/env python

'''
Helper classes for manipulating single frames of video for a PiWall.
'''
import cv2
import pdb

# Helper classes
from utils import FilenameSequence, ImageViewer

class Frame:
    '''Container for an openCV image in general.'''
    def __init__(self, img):
        self.img = img
        (h,w) = img.shape[:2]
        self.h_original = h
        self.w_original = w
        self.scaled_images = {}
        
    def scaleW(self, w):
        # Ratio
        r = w / self.img.shape[1]
        # New Dimensions, preserving ratio
        h = int(self.img.shape[0]*r)
        dim = (w, h)
        scaled = cv2.resize(self.img, dim, interpolation = cv2.INTER_AREA)
        self.scaled_images[(h,w)] = scaled
        return scaled
    
def overlay(self, original, target):
    '''Take original and overlay on target (assumed black). Cropping window size is taken from target.   Options to slide the cropping window within the image.'''
    (oy,ox) = original.shape[:2]
    (ty,tx) = target.shape[:2]
    # First find the ROI, or all of the image if target is larger : cx is the cropping size
    if tx >= ox:
        cx = ox
        dx = 0
    else:
        cx = tx
        dx = int((ox - tx)/2)
    if ty >= oy:
        cy = oy
        dy = 0
    else:
        cy = ty
        dy = int((oy-ty)/2)
    roi = original[dx:dx+cx, dy:dy+cy]
    # Now superimpose the roi on the target
    # Study the bitwise operations tutorial to get the nag of settig up masks and adding images.
    
def main():
    im = cv2.imread('data/jurassic-original.png')
    s1 = im.shape
    print s1
    w1 = ImageViewer(im)
    w1.windowShow()
    F = Frame(im)
    s = F.scaleW(s1[1]*2)
    w2 = ImageViewer(s)
    print s.shape
    w2.windowShow()

if __name__ == '__main__':
    main()
