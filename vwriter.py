#!/usr/bin/env python

# Utility to render a bunch of images to a video (avi)

# import the necessary packages
from __future__ import print_function
#from imutils.video import VideoStream
import numpy as np
import argparse
#import imutils
import time
import cv2
import sys


class VideoWriterRGB:
    def __init__(self, output='video.avi', fps=20, codec=["M", "J", "P", "G"]):
        self.output = output
        self.fps = fps
        self.codec = codec
        self.fourcc = cv2.VideoWriter_fourcc(*self.codec)
        self.writer = None
        (self.h, self.w) = (None, None)
        self.zeros = None

    def addFrame(self, frame, width=300):
        frame = imutils.resize(frame, width)

        # check if the writer is None
        if self.writer is None:
            # store the image dimensions, initialzie the video writer,
            # and construct the zeros array
            (self.h, self.w) = frame.shape[:2]
            self.writer = cv2.VideoWriter(self.output, self.fourcc, self.fps,
                                          (self.w * 2, self.h * 2), True)
            self.zeros = np.zeros((self.h, self.w), dtype="uint8")

        # break the image into its RGB components, then construct the
        # RGB representation of each frame individually
        (B, G, R) = cv2.split(frame)
        R = cv2.merge([self.zeros, self.zeros, R])
        G = cv2.merge([self.zeros, G, self.zeros])
        B = cv2.merge([B, self.zeros, self.zeros])

        # construct the final output frame, storing the original frame
        # at the top-left, the red channel in the top-right, the green
        # channel in the bottom-right, and the blue channel in the
        # bottom-left
        output = np.zeros((self.h * 2, self.w * 2, 3), dtype="uint8")
        output[0:self.h, 0:self.w] = frame
        output[0:self.h, self.w:self.w * 2] = R
        output[self.h:self.h * 2, self.w:self.w * 2] = G
        output[self.h:self.h * 2, 0:self.w] = B

        # write the output frame to file
        self.writer.write(output)

    def finalise(self):
        self.writer.release()


class VideoWriter:
    def __init__(self, output='video.avi', fps=20, codec=["M", "J", "P", "G"]):
        self.output = output
        self.fps = fps
        self.codec = codec
        self.fourcc = cv2.VideoWriter_fourcc(*self.codec)
        self.writer = None
        (self.h, self.w) = (None, None)

    def addFrame(self, frame, width=600):
        frame = imutils.resize(frame, width)

        # check if the writer is None
        if self.writer is None:
            # store the image dimensions, initialzie the video writer,
            (self.h, self.w) = frame.shape[:2]
            self.writer = cv2.VideoWriter(self.output, self.fourcc, self.fps,
                                          (self.w, self.h), True)
        # write the output frame to file
        self.writer.write(frame)

    def finalise(self):
        self.writer.release()


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--output", required=True,
                    help="path to output video file")
    ap.add_argument("-p", "--picamera", type=int, default=-1,
                    help="whether or not the Raspberry Pi camera should be used")
    ap.add_argument("-f", "--fps", type=int, default=20,
                    help="FPS of output video")
    ap.add_argument("-c", "--codec", type=str, default="MJPG",
                    help="codec of output video")
    args = vars(ap.parse_args())
    img = cv2.imread('./data/hi.jpg')
    vwriter = VideoWriterRGB('hi-video.avi')
    frames = 0
    for angle in range(0, 360, 5):
        rot = imutils.rotate(img, angle=angle)
        cv2.imshow("Angle = %d" % (angle), rot)
        vwriter.addFrame(rot)
        frames += 1
    for angle in range(360, 0, -5):
        rot = imutils.rotate(img, angle=angle)
        cv2.imshow("Angle = %d" % (angle), rot)
        vwriter.addFrame(rot)
        frames += 1
    vwriter.finalise()
    print("Created movie with %d frames" % frames)
