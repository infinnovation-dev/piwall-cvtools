#!/usr/bin/env python

'''
Video capture sample : originally taken from OpenCV-3.1.0/samples and expanded.

Sample shows how VideoCapture class can be used to acquire video
frames from a camera of a movie file. Also the sample provides
an example of procedural video generation by an object, mimicking
the VideoCapture interface (see Chess class).

'create_capture' is a convinience function for capture creation,
falling back to procedural video in case of error.

Usage:
    video.py [--shotdir <shot path>] [source0] [source1] ...'

    sourceN is an
     - integer number for camera capture
     - name of video file
     - synth:<params> for procedural video

Synth examples:
    synth:bg=../data/lena.jpg:noise=0.1
    synth:class=chess:bg=../data/lena.jpg:noise=0.1:size=640x480

Keys:
    ESC    - exit
    SPACE  - save current frame to <shot path> directory

'''

# Python 2/3 compatibility
from __future__ import print_function

import numpy as np
from numpy import pi, sin, cos

import cv2

# built-in modules
import os
from time import clock
import pdb

# local modules
import common

class VideoSynthBase(object):
    def __init__(self, size=None, noise=0.0, bg = None, **params):
        self.bg = None
        self.frame_size = (640, 480)
        if bg is not None:
            self.bg = cv2.imread(bg, 1)
            h, w = self.bg.shape[:2]
            self.frame_size = (w, h)

        if size is not None:
            w, h = map(int, size.split('x'))
            self.frame_size = (w, h)
            if self.bg is not None:
                self.bg = cv2.resize(self.bg, self.frame_size)

        self.noise = float(noise)

    def render(self, dst):
        pass

    def read(self, dst=None):
        w, h = self.frame_size

        if self.bg is None:
            buf = np.zeros((h, w, 3), np.uint8)
        else:
            buf = self.bg.copy()

        self.render(buf)

        if self.noise > 0.0:
            noise = np.zeros((h, w, 3), np.int8)
            cv2.randn(noise, np.zeros(3), np.ones(3)*255*self.noise)
            buf = cv2.add(buf, noise, dtype=cv2.CV_8UC3)
        return True, buf

    def isOpened(self):
        return True

class Chess(VideoSynthBase):
    def __init__(self, **kw):
        super(Chess, self).__init__(**kw)

        w, h = self.frame_size

        self.grid_size = sx, sy = 10, 7
        white_quads = []
        black_quads = []
        for i, j in np.ndindex(sy, sx):
            q = [[j, i, 0], [j+1, i, 0], [j+1, i+1, 0], [j, i+1, 0]]
            [white_quads, black_quads][(i + j) % 2].append(q)
        self.white_quads = np.float32(white_quads)
        self.black_quads = np.float32(black_quads)

        fx = 0.9
        self.K = np.float64([[fx*w, 0, 0.5*(w-1)],
                        [0, fx*w, 0.5*(h-1)],
                        [0.0,0.0,      1.0]])

        self.dist_coef = np.float64([-0.2, 0.1, 0, 0])
        self.t = 0

    def draw_quads(self, img, quads, color = (0, 255, 0)):
        img_quads = cv2.projectPoints(quads.reshape(-1, 3), self.rvec, self.tvec, self.K, self.dist_coef) [0]
        img_quads.shape = quads.shape[:2] + (2,)
        for q in img_quads:
            cv2.fillConvexPoly(img, np.int32(q*4), color, cv2.LINE_AA, shift=2)

    def render(self, dst):
        t = self.t
        self.t += 1.0/30.0

        sx, sy = self.grid_size
        center = np.array([0.5*sx, 0.5*sy, 0.0])
        phi = pi/3 + sin(t*3)*pi/8
        c, s = cos(phi), sin(phi)
        ofs = np.array([sin(1.2*t), cos(1.8*t), 0]) * sx * 0.2
        eye_pos = center + np.array([cos(t)*c, sin(t)*c, s]) * 15.0 + ofs
        target_pos = center + ofs

        R, self.tvec = common.lookat(eye_pos, target_pos)
        self.rvec = common.mtx2rvec(R)

        self.draw_quads(dst, self.white_quads, (245, 245, 245))
        self.draw_quads(dst, self.black_quads, (10, 10, 10))

class TestCard(VideoSynthBase):
    def __init__(self, **kw):
        super(TestCard, self).__init__(**kw)

        w, h = self.frame_size

        self.grid_size = sx, sy = 16,9
        self.t = 0

    def render(self, dst):
        t = self.t
        self.t += 1.0/30.0
        
        l = 120
        black = [245,245,245]
        white = [10,10,10]
        colors = [black,white]
        nsq = 0
        x = 0
        for xs in range(0,16):
            y = 0
            for ys in range(0,9):
                fg = colors[nsq%2]
                bg = colors[(nsq+1) % 2]
                dst[y:y+l,x:x+l] = bg
                cv2.putText(dst, "%s" % nsq, (x+l/4, y+2*l/3), cv2.FONT_HERSHEY_PLAIN, 3, [0,0,255], thickness = 2, lineType=cv2.LINE_AA)
                y+=l
                nsq+=1
            x+=l

class Album(VideoSynthBase):
    def __init__(self, *args, **kw):
        '''Takes a list of image paths (album=['fn1.jpg', 'fn2.jpg', ...]) from which to generate the next read() result. Lazy evaluation.  If loop=True, loop.''' 
        super(Album, self).__init__(**kw)
        w, h = self.frame_size
        self.bufs = []
        fnsAsCsv = kw['album']
        for fn in fnsAsCsv.split(","):
            if os.path.exists(fn):
                self.bufs.append([fn, None])
            else:
                pass
        self.nImages = len(self.bufs)
        self.nextImage = 0
        if 'loop' in kw:
            self.loop = kw['loop']
        else:
            self.loop = False

    def read(self, dst=None):
        n = self.nextImage
        if n == self.nImages:
            if self.loop:
                n = 0
            else:
                return False, None
        (fn, buf) = self.bufs[n]
        if buf:
            return True, buf
        else:
            try:
                buf = cv2.resize(cv2.imread(fn), self.frame_size)
            except:
                buf = np.zeros((h,w,3), np.uint8)
        self.bufs[n] = [n, buf]
        self.nextImage += 1
        return True, buf

classes = dict(chess=Chess, album=Album, testcard=TestCard)

presets = dict(
    empty = 'synth:',
    lena = 'synth:bg=../data/lena.jpg:noise=0.1',
    chess = 'synth:class=chess:bg=../data/lena.jpg:noise=0.1:size=640x480'
)


def create_capture(source = 0, fallback = presets['chess']):
    '''source: <int> or '<int>|<filename>|synth [:<param_name>=<value> [:...]]'
    '''
    source = str(source).strip()
    chunks = source.split(':')
    # handle drive letter ('c:', ...)
    if len(chunks) > 1 and len(chunks[0]) == 1 and chunks[0].isalpha():
        chunks[1] = chunks[0] + ':' + chunks[1]
        del chunks[0]

    source = chunks[0]
    try: source = int(source)
    except ValueError: pass
    params = dict( s.split('=') for s in chunks[1:] )

    cap = None
    if source == 'synth':
        Class = classes.get(params.get('class', None), VideoSynthBase)
        try: cap = Class(**params)
        except: pass
    else:
        cap = cv2.VideoCapture(source)
        if 'size' in params:
            w, h = map(int, params['size'].split('x'))
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
    if cap is None or not cap.isOpened():
        print('Warning: unable to open video source: ', source)
        if fallback is not None:
            return create_capture(fallback, None)
    return cap

if __name__ == '__main__':
    import sys
    import getopt

    print(__doc__)

    args, sources = getopt.getopt(sys.argv[1:], '', 'shotdir=')
    args = dict(args)
    shotdir = args.get('--shotdir', '.')
    if len(sources) == 0:
        sources = [ 0 ]

    caps = list(map(create_capture, sources))
    shot_idx = 0
    while True:
        imgs = []
        for i, cap in enumerate(caps):
            ret, img = cap.read()
            imgs.append(img)
            cv2.imshow('capture %d' % i, img)
        ch = 0xFF & cv2.waitKey(1)
        if ch == 27:
            break
        if ch == ord(' '):
            for i, img in enumerate(imgs):
                fn = '%s/shot_%d_%03d.bmp' % (shotdir, i, shot_idx)
                cv2.imwrite(fn, img)
                print(fn, 'saved')
            shot_idx += 1
    cv2.destroyAllWindows()
