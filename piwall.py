#!/usr/bin/env python

'''
Prototype .piwall generator to find monitor geometry from photograph of a piwall.

Can operate sequentially on a set of photos to compare and contrast results.

Commit  Summary
- 
        Repeat test of the basic rectangle matching (c055d3a) against red backgrounds. 
-
c055d3a Basic demonstration of the rectangle matching taken from the OpenCV 3.1 samples code applied to a video.
        See https://www.youtube.com/watch?v=pETFBrweeAc&feature=youtu.be
-
'''

# TODO: complete the plugins concept.  THERE MUST BE A BETTER WAY.
# TODO: replace "square" by "rectangle" throughout.

import math
from itertools import count
import glob
import os
import sys

# Python 2/3 compatibility
PY3 = sys.version_info[0] == 3

if PY3:
    xrange = range

import numpy as np
import warnings;
with warnings.catch_warnings():
    warnings.simplefilter("ignore"); 
    from matplotlib import pyplot as plt

import cv2
import pdb
import time

from skimage.measure import structural_similarity as ssim
from skimage.measure import compare_ssim


sys.path.append(os.path.expanduser('~/pd/opencv/opencv-3.1.0/samples/python/'))
from video import create_capture, Album
from time import clock

# Record the results of processing the video using vwriter
from vwriter import VideoWriter

# Helper classes
from utils import FilenameSequence, ImageViewer

# Convert located wall coordinates into model space
from model import Wall, Tile

#####################################################################################################################
# Utility Functions
#####################################################################################################################

class Rectangle:
    def __init__(self, xl, xr, yl, yu):
        self.xl = xl
        self.xr = xr
        self.yl = yl
        self.yu = yu

    def asContour(self):
        xl = self.xl
        xr = self.xr
        yl = self.yl
        yu = self.yu
        return np.array([(xl,yl), (xl, yu), (xr,yu), (xr, yl)], dtype = np.int)
    
    def getRoi(self, img):
        return img[self.xl:self.xr, self.yl:self.yu,:]
        
def hdSolidBlock(fn = "redHDSolidBlock.jpg", bgr = None):
    '''Generate test images as solid blocks of colour of known size, save to filename fn.'''
    # Create a zero (black) image of HD size with 3 colour dimensions.  Colour space assumed BGR by default.
    h = 1080
    w = 1920
    img = np.zeros((h,w,3),dtype="uint8")
    # Want to set all of the pixels to bgr tuple, default red, 8 bit colour
    if not bgr:
        bgr = [0,0,255]
    img[:,:] = bgr
    vw = ImageViewer(img)
    vw.windowShow()
    #cv2.imshow("zeroes", frame)
    #ch = 0xff & cv2.waitKey(10000)
    #cv2.destroyAllWindows()
    cv2.imwrite(fn, img)
    
def draw_str(dst, target, s, scale):
    x, y = target
    cv2.putText(dst, s, (x+1, y+1), cv2.FONT_HERSHEY_PLAIN, scale, (0, 0, 0), thickness = 2, lineType=cv2.LINE_AA)
    cv2.putText(dst, s, (x, y), cv2.FONT_HERSHEY_PLAIN, scale, (255, 255, 255), lineType=cv2.LINE_AA)

def angle_cos(p0, p1, p2):
    d1, d2 = (p0-p1).astype('float'), (p2-p1).astype('float')
    return abs( np.dot(d1, d2) / np.sqrt( np.dot(d1, d1)*np.dot(d2, d2) ) )

###
### Sample code, with commentary added.
###

def find_squares(img, cos_limit = 0.1):
    print('search for squares with threshold %f' % cos_limit)
    img = cv2.GaussianBlur(img, (5, 5), 0)
    squares = []
    for gray in cv2.split(img):
        for thrs in xrange(0, 255, 26):
            if thrs == 0:
                bin = cv2.Canny(gray, 0, 50, apertureSize=5)
                bin = cv2.dilate(bin, None)
            else:
                retval, bin = cv2.threshold(gray, thrs, 255, cv2.THRESH_BINARY)
            bin, contours, hierarchy = cv2.findContours(bin, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                cnt_len = cv2.arcLength(cnt, True)
                cnt = cv2.approxPolyDP(cnt, 0.02*cnt_len, True)
                if len(cnt) == 4 and cv2.contourArea(cnt) > 1000 and cv2.isContourConvex(cnt):
                    cnt = cnt.reshape(-1, 2)
                    max_cos = np.max([angle_cos( cnt[i], cnt[(i+1) % 4], cnt[(i+2) % 4] ) for i in xrange(4)])
                    if max_cos < cos_limit :
                        squares.append(cnt)
                    else:
                        #print('dropped a square with max_cos %f' % max_cos)
                        pass
    return squares

###
### Version V2.  Collect meta-data along the way,  with commentary added.
###

class Square(object):
    '''Wrapper for contour and associated information'''
    _nOf = count(0)
    def __init__(self, contour, area = None, isConvex = False, max_cos = -1):
        self.ID = self._nOf.next()
        self.contour = contour
        self.area = area
        self.isConvex = isConvex
        self.max_cos = max_cos

    def __repr__(self):
        s = []
        s.append('Square %04d : area = %d : max_cos = %f : shape = %s : contour = %s' % (self.ID, self.area, self.max_cos, self.contour.shape, self.contour))
        return '\n'.join(s)

def find_squares_V2(img, cos_limit = 0.1, area_min = 1000, area_max = 1E9, show = False, info = False, destroy = True, thumbnailDir = None):
    if thumbnailDir:
        os.mkdir(thumbnailDir)
        prefix = '%s/fsv2' % thumbnailDir
    else:
        prefix = 'fsv2'
    tgen = FilenameSequence(prefix, 'jpg')
    print('search for squares with threshold %f' % cos_limit)
    title = tgen.next('original')
    if show:ImageViewer(img).show(window=title, destroy = destroy, info = info, thumbnailfn = title)
    # Smooth/Blurr to reduce/smear out noise
    img = cv2.GaussianBlur(img, (5, 5), 0)
    title = tgen.next('gaussian-blur')
    if show: ImageViewer(img).show(window=title, destroy = destroy, info = info, thumbnailfn = title)
    # Collect the contours matching area, side, angle filters as squares
    squares = []
    # Attempt to match edges found in blue, green or red channels : collect all
    channel = 0
    for gray in cv2.split(img):
        channel += 1
        print('channel %d ' % channel)
        title = tgen.next('channel-%d' % channel)
        if show: ImageViewer(gray).show(window = title, destroy = destroy, info = info, thumbnailfn = title)
        for thrs in xrange(0, 255, 26):
            print('Using threshold %d' % thrs)
            if thrs == 0:
                print('First step')
                bin = cv2.Canny(gray, 0, 50, apertureSize=5)
                title = tgen.next('canny-%d' % channel)
                if show: ImageViewer(bin).show(window = title, destroy = destroy, info = info, thumbnailfn = title)
                bin = cv2.dilate(bin, None)
                title = tgen.next('canny-dilate-%d' % channel)
                if show: ImageViewer(bin).show(window = title, destroy = destroy, info = info, thumbnailfn = title)
            else:
                retval, bin = cv2.threshold(gray, thrs, 255, cv2.THRESH_BINARY)
                title = tgen.next('channel-%d-threshold-%d' % (channel, thrs))
                if show: ImageViewer(bin).show(window='Next threshold (n to continue)', destroy = destroy, info = info, thumbnailfn = title)
            bin, contours, hierarchy = cv2.findContours(bin, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            title = tgen.next('channel-%d-threshold-%d-contours' % (channel, thrs))
            if show: ImageViewer(bin).show(window = title, destroy = destroy, info = info, thumbnailfn = title)
            for cnt in contours:
                cnt_len = cv2.arcLength(cnt, True)
                cnt = cv2.approxPolyDP(cnt, 0.02*cnt_len, True)
                cnt_len = len(cnt)
                cnt_area = cv2.contourArea(cnt)
                cnt_isConvex = cv2.isContourConvex(cnt)
                if cnt_len == 4 and (cnt_area > area_min and cnt_area < area_max)  and cnt_isConvex:
                    cnt = cnt.reshape(-1, 2)
                    max_cos = np.max([angle_cos( cnt[i], cnt[(i+1) % 4], cnt[(i+2) % 4] ) for i in xrange(4)])
                    if max_cos < cos_limit :
                        sq = Square(cnt, cnt_area, cnt_isConvex, max_cos)
                        squares.append(sq)
                    else:
                        #print('dropped a square with max_cos %f' % max_cos)
                        pass
    return squares

###
### Version V3.  Look to investigate alternative options and also track the action.  Refactored as a class.
###

### Contours identified manually from Gimp to see if pixel coordinates this way are accurate.
gimpContours = {
    'image-filename':
    {'feature' : ['xl','xr','yl','yu']},
    '2x2-red-1.jpg':
    {'top-left-monitor' : [104,520,508,776]}
}

class SquareFinderV3:

    def __init__(self, img, cos_limit = 0.1, area_min = 1000, area_max = 1E9, show = False, info = False, destroy = True, thumbnailDir = None, imgPath = None):
        self.img = img
        self.cos_limit = cos_limit
        self.area_min = area_min
        self.area_max = area_max
        self.show = show
        self.info = info
        self.destroy = destroy
        self.thumbnailDir = thumbnailDir
        # optional metadata.
        self.imgPath = imgPath
        # Initialise that which will be found through exploitation of the class
        self.mode = 0
        self.modeDesc = 'No option selected'
        self.squares = []
        self.rois = {}
        # Kick Off.
        self.commonStart()

    def find(self, mode):
        self.mode = mode
        if mode == 1:
            self.modeDesc = 'Run gaussianBlur(), then cannyThresholding'
            self.gaussianBlur()
            self.cannyThresholding()
        elif mode == 2:
            # Check Gimp Hints
            self.gimpMarkup()
            #self.cannyThresholding()
            self.modeDesc = 'Run gimpMarkup'
        elif mode == 3:
            # Massively mask red as a precursor phase
            self.gaussianBlur()
            self.colourMapping()
            self.solidRedFilter()
            #self.cannyThresholding()
            self.modeDesc = 'Run gaussianBlur(), colourMapping(), solidRedFilter(), #cannyThresholding'
        elif mode == 4:
            self.modeDesc = 'Run gaussianBlur(), then cannyThresholding with RETR_EXTERNAL contour removal mode'
            self.gaussianBlur()
            self.cannyThresholding(cv2.RETR_EXTERNAL)
        elif mode == 5:
            self.modeDesc = 'Run gaussianBlur(), then cannyThresholding with RETR_TREE contour removal mode'
            self.gaussianBlur()
            self.cannyThresholding(cv2.RETR_TREE)
# Apply Heuristics to filter out false
        self.squares = filterContoursRemove(self.img, self.squares)
        return self.squares
    
    def commonStart(self):
        if self.thumbnailDir:
            if not os.path.exists(self.thumbnailDir):
                os.mkdir(self.thumbnailDir)
            prefix = '%s/fsv2' % self.thumbnailDir
        else:
            prefix = 'fsv2'
        self.tgen = FilenameSequence(prefix, 'jpg')
        print('search for squares with threshold %f' % self.cos_limit)
        title = self.tgen.next('original')
        if self.show:ImageViewer(self.img).show(window=title, destroy = self.destroy, info = self.info, thumbnailfn = title)
    
    def gaussianBlur(self):
        # Smooth/Blurr to reduce/smear out noise
        self.img = cv2.GaussianBlur(self.img, (5, 5), 0)
        title = self.tgen.next('gaussian-blur')
        if self.show: ImageViewer(self.img).show(window=title, destroy = self.destroy, info = self.info, thumbnailfn = title)
    
    def gimpMarkup(self, hints = gimpContours, image = "2x2-red-1.jpg", feature = "top-left-monitor"):
        r = Rectangle(*hints[image][feature])
        contour = r.asContour()
        cv2.drawContours(self.img, [contour], -1, (0, 255, 0), 5 )
        title = self.tgen.next(feature)
        if self.show: ImageViewer(self.img).show(window=title, destroy = self.destroy, info = self.info, thumbnailfn = title)
        roi = r.getRoi(self.img)
        self.rois[feature] = roi
        # Histogram the ROI to get the spread of intensities, in each channel and grayscale
        title = '%s-roi.jpg' % feature
        if self.show: ImageViewer(roi).show(window=title, destroy = self.destroy, info = self.info, thumbnailfn = title)
        colors = ('b','g','r')
        for i,col in enumerate(colors):
            hist = cv2.calcHist([roi], [i], None, [256], [0,256])
            plt.plot(hist, color = col)
            plt.xlim([0,256])
            #plt.hist(roi.ravel(), 256, [0,256])
        plt.show()
        cmap = ColorMapper(roi)
        cmap.mapit(1)
        title = self.tgen.next('colourMapping')
        if self.show: ImageViewer(self.img).show(window=title, destroy = self.destroy, info = self.info, thumbnailfn = title)
        cv2.waitKey()

    def colourMapping(self):
        cmap = ColorMapper(self.img)
        title = self.tgen.next('colourMapping')
        if self.show: ImageViewer(self.img).show(window=title, destroy = self.destroy, info = self.info, thumbnailfn = title)

    def solidRedFilter(self):
        # find all the 'red' shapes in the image
        lower = np.array([0, 0, 0])
        upper = np.array([15, 15, 15])
        self.img = cv2.inRange(self.img, lower, upper)
        title = self.tgen.next('solidRedFilter')
        if self.show: ImageViewer(self.img).show(window=title, destroy = self.destroy, info = self.info, thumbnailfn = title)
        
    def cannyThresholding(self, contour_retrieval_mode = cv2.RETR_LIST):
        '''
        contour_retrieval_mode is passed through as second argument to cv2.findContours
        '''
    
        # Attempt to match edges found in blue, green or red channels : collect all
        channel = 0
        for gray in cv2.split(self.img):
            channel += 1
            print('channel %d ' % channel)
            title = self.tgen.next('channel-%d' % channel)
            if self.show: ImageViewer(gray).show(window = title, destroy = self.destroy, info = self.info, thumbnailfn = title)
            found = {}
            for thrs in xrange(0, 255, 26):
                print('Using threshold %d' % thrs)
                if thrs == 0:
                    print('First step')
                    bin = cv2.Canny(gray, 0, 50, apertureSize=5)
                    title = self.tgen.next('canny-%d' % channel)
                    if self.show: ImageViewer(bin).show(window = title, destroy = self.destroy, info = self.info, thumbnailfn = title)
                    bin = cv2.dilate(bin, None)
                    title = self.tgen.next('canny-dilate-%d' % channel)
                    if self.show: ImageViewer(bin).show(window = title, destroy = self.destroy, info = self.info, thumbnailfn = title)
                else:
                    retval, bin = cv2.threshold(gray, thrs, 255, cv2.THRESH_BINARY)
                    title = self.tgen.next('channel-%d-threshold-%d' % (channel, thrs))
                    if self.show: ImageViewer(bin).show(window='Next threshold (n to continue)', destroy = self.destroy, info = self.info, thumbnailfn = title)
                bin, contours, hierarchy = cv2.findContours(bin, contour_retrieval_mode, cv2.CHAIN_APPROX_SIMPLE)
                title = self.tgen.next('channel-%d-threshold-%d-contours' % (channel, thrs))
                if self.show: ImageViewer(bin).show(window = title, destroy = self.destroy, info = self.info, thumbnailfn = title)
                if contour_retrieval_mode == cv2.RETR_LIST or contour_retrieval_mode == cv2.RETR_EXTERNAL:
                    filteredContours = contours
                else:
                    filteredContours = []
                    h = hierarchy[0]
                    for component in zip(contours, h):
                        currentContour = component[0]
                        currentHierarchy = component[1]
                        if currentHierarchy[3] < 0:
                            # Found the outermost parent component
                            filteredContours.append(currentContour)
                    print('Contours filtered.   Input %d  Output %d' % (len(contours), len(filteredContours)))
                    time.sleep(5)
                for cnt in filteredContours:
                    cnt_len = cv2.arcLength(cnt, True)
                    cnt = cv2.approxPolyDP(cnt, 0.02*cnt_len, True)
                    cnt_len = len(cnt)
                    cnt_area = cv2.contourArea(cnt)
                    cnt_isConvex = cv2.isContourConvex(cnt)
                    if cnt_len == 4 and (cnt_area > self.area_min and cnt_area < self.area_max)  and cnt_isConvex:
                        cnt = cnt.reshape(-1, 2)
                        max_cos = np.max([angle_cos( cnt[i], cnt[(i+1) % 4], cnt[(i+2) % 4] ) for i in xrange(4)])
                        if max_cos < self.cos_limit :
                            sq = Square(cnt, cnt_area, cnt_isConvex, max_cos)
                            self.squares.append(sq)
                        else:
                            #print('dropped a square with max_cos %f' % max_cos)
                            pass
                found[thrs] = len(self.squares)
                print('Found %d quadrilaterals with threshold %d' % (len(self.squares), thrs))

    def __repr__(self):
        s = []
        s.append('PiWall geometry finder class : %s ' % self.__class__.__name__)
        s.append('Input image path : %s ' % self.imgPath)
        s.append('Mode             : %d ' % self.mode)
        s.append('\t%s' % self.modeDesc)
        s.append('cosine limit     : %f ' % self.cos_limit)
        s.append('area min         : %d <%d side>' % (self.area_min, int(math.sqrt(self.area_min))))
        s.append('area max         : %d <%d side>' % (self.area_max, int(math.sqrt(self.area_max))))
        s.append('squares found    : %d' % len(self.squares))
        for (i  ,sq) in enumerate(self.squares):
            s.append('\tsquare[%d]     : area %d max_cos %f' % (i, sq.area, sq.max_cos))
        return '\n'.join(s)

    
def contour_to_monitor_coords(screenCnt):
    '''Apply pyimagesearch algorithm to identify tl,tr,br,bl points from a contour'''
    # now that we have our screen contour, we need to determine
    # the top-left, top-right, bottom-right, and bottom-left
    # points so that we can later warp the image -- we'll start
    # by reshaping our contour to be our finals and initializing
    # our output rectangle in top-left, top-right, bottom-right,
    # and bottom-left order
    pts = screenCnt.reshape(4, 2)
    rect = np.zeros((4, 2), dtype = "float32")
    
    # the top-left point has the smallest sum whereas the
    # bottom-right has the largest sum
    s = pts.sum(axis = 1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    
    # compute the difference between the points -- the top-right
    # will have the minumum difference and the bottom-left will
    # have the maximum difference
    diff = np.diff(pts, axis = 1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]

    return rect

def compute_warp(rect):    
    
    # now that we have our rectangle of points, let's compute
    # the width of our new image
    (tl, tr, br, bl) = rect
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    
    # ...and now for the height of our new image
    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    
    # take the maximum of the width and height values to reach
    # our final dimensions
    maxWidth = max(int(widthA), int(widthB))
    maxHeight = max(int(heightA), int(heightB))
    
    # construct our destination points which will be used to
    # map the screen to a top-down, "birds eye" view
    dst = np.array([
	[0, 0],
	[maxWidth - 1, 0],
	[maxWidth - 1, maxHeight - 1],
	[0, maxHeight - 1]], dtype = "float32")
    
    # calculate the perspective transform matrix and warp
    # the perspective to grab the screen
    M = cv2.getPerspectiveTransform(rect, dst)

    return (maxWidth, maxHeight, dst, M)

def do_warp(M, warp):
    warp = cv2.warpPerspective(orig, M, (maxWidth, maxHeight))
    # convert the warped image to grayscale and then adjust
    # the intensity of the pixels to have minimum and maximum
    # values of 0 and 255, respectively
    warp = cv2.cvtColor(warp, cv2.COLOR_BGR2GRAY)
    warp = exposure.rescale_intensity(warp, out_range = (0, 255))
    
    # the pokemon we want to identify will be in the top-right
    # corner of the warped image -- let's crop this region out
    (h, w) = warp.shape
    (dX, dY) = (int(w * 0.4), int(h * 0.45))
    crop = warp[10:dY, w - dX:w - 10]
    
    # save the cropped image to file
    cv2.imwrite("cropped.png", crop)
    
    # show our images
    cv2.imshow("image", image)
    cv2.imshow("edge", edged)
    cv2.imshow("warp", imutils.resize(warp, height = 300))
    cv2.imshow("crop", imutils.resize(crop, height = 300))
    cv2.waitKey(0)

def classify_monitor_contour_set(contours):
    '''Not a general purpose function : given the expectation of a set of strongly related contours for one monitor...'''
    # First pass : compute the center of mass of every contour
    classified = {}
    for (i,c) in enumerate(contours):
        classified[i] = {}
        classified[i]['contour'] = c
        moments = M = cv2.moments(c)
        classified[i]['com'] = (int(M['m10']/M['m00']), int(M['m01']/M['m00']))
        rect = contour_to_monitor_coords(c)
        (maxWidth, maxHeight, dest, Mwarp) = compute_warp(rect)
        classified[i]['rect'] = rect
        classified[i]['maxWidth'] = maxWidth
        classified[i]['maxHeight'] = maxHeight
        classified[i]['dest'] = dest
        classified[i]['Mwarp'] = Mwarp
    # Second pass : establish if c-o-m of every contour is within the first contour
    reference_contour = contours[0]
    for (i,c) in enumerate(contours):
        classified[i]['coherent'] = cv2.pointPolygonTest(reference_contour, classified[i]['com'], False)
    # Final pass : report on the set
    print('$'*80)
    for (i,c) in enumerate(contours):
        print('%d : c-o-m %s : coherent : %d mw %d mh %d' % (i,
                                                             classified[i]['com'],
                                                             classified[i]['coherent'],
                                                             classified[i]['maxWidth'],
                                                             classified[i]['maxHeight'],
        ))
    print('$'*80)
    # From the contours coherent to the reference contour, build an average/best estimator
    count = 0
    rect = np.zeros((4, 2), dtype = "float32")            
    for (i,c) in enumerate(contours):
        if classified[i]['coherent'] == 1:
            count += 1
            for j in range(0,4):
                rect[j] += classified[i]['rect'][j]
    #pdb.set_trace()
    for j in range(0,4):
        # BUG to show Alison
        # rect[j] = (rect[j]/1.0*count).astype('uint8')
        rect[j] = (rect[j]/(1.0*count)).astype('uint32')
    time.sleep(2.5)
    return rect

def classify_multi_monitors_contour_set(contours):
    '''Not a general purpose function : given the expectation of a set of strongly related contours for one monitor...
    Extension from classify_monitor_contour set where the contours span multiple sets of monitors.
    '''
    # First pass : compute the center of mass of every contour, also track the mean of the maxWidth/maxHeight
    classified = {}
    maxWidthTotal = 0
    maxHeightTotal = 0
    classifiedBins = []
    for (i,c) in enumerate(contours):
        classified[i] = {}
        classified[i]['contour'] = c
        moments = M = cv2.moments(c)
        (x, y) = (int(M['m10']/M['m00']), int(M['m01']/M['m00']))
        classified[i]['com'] = (x, y)
        comDistanceFromOrigin = math.sqrt(x**2+y**2)
        classified[i]['dfo'] = comDistanceFromOrigin
        classifiedBins.append((i,comDistanceFromOrigin))
        rect = contour_to_monitor_coords(c)
        (maxWidth, maxHeight, dest, Mwarp) = compute_warp(rect)
        maxWidthTotal += maxWidth
        maxHeightTotal += maxHeight
        classified[i]['rect'] = rect
        classified[i]['maxWidth'] = maxWidth
        classified[i]['maxHeight'] = maxHeight
        classified[i]['dest'] = dest
        classified[i]['Mwarp'] = Mwarp
    # Intermediate: report on the set
    print('$'*80)
    for (i,c) in enumerate(contours):
        if (i > 0) :
            print('%d : c-o-m %s (delta %s) : mw %d mh %d' % (i,
                                                              classified[i]['com'],
                                                              (int(classified[i]['dfo']) - int(classified[i-1]['dfo'])),
                                                              classified[i]['maxWidth'],
                                                              classified[i]['maxHeight']
            ))
        else:
            print('%d : c-o-m %s : mw %d mh %d' % (i,
                                                   classified[i]['com'],
                                                   classified[i]['maxWidth'],
                                                   classified[i]['maxHeight']
            ))
    print('$'*80)
    # Second pass : sort the classified contours into bins to distinguish groups that map to a given monitor
    meanMaxWidth = int(maxWidthTotal*1.0/len(contours))
    meanMaxHeight =  int(maxHeightTotal*1.0/len(contours))
    binSeparation = 0.1*min(meanMaxWidth, meanMaxHeight)
    def cbcmp(x,y):
        if x[1] == y[1]:
            return 0
        else:
            return int((x[1] - y[1]) / abs(x[1] - y[1]))
    classifiedBins.sort(cbcmp)
    print('sorted')
    bins = []
    bins.append(classifiedBins[0])
    dist = classifiedBins[0][1]
    bestContours = []
    count = 0
    rect = np.zeros((4,2), dtype = "float32")
    for (index, distance) in classifiedBins[1:]:
        if abs(distance - dist) > binSeparation:
            bins.append((index,distance))
            dist = distance
            print('Found the next bin with distance %s' % dist)
            for j in range(0,4):
                rect[j] = (rect[j]/(1.0*count)).astype('uint32')
            bestContours.append((rect, count))
            count = 0
            rect = np.zeros((4,2), dtype = "float32")
        else:
            count += 1
            for j in range(0,4):
                rect[j] += classified[index]['rect'][j]
            print('Found another estimator in the same bin')
    # Special case : handle the last set
    bins.append((index,distance))
    dist = distance
    print('Found the next bin with distance %s' % dist)
    for j in range(0,4):
        rect[j] = (rect[j]/(1.0*count)).astype('uint32')
    bestContours.append((rect, count))
    print('Found %d bestContours as estimators of the borders of the monitors' % len(bestContours))
    return bestContours

# cv2.findContours tracks continuous points with same intensity, extracted from a binary image 
#
# First phase produces the basic canny edge detection (could substitut eother edge/feature detectors)

class ColorMapper:
    '''Class to use masks and histograms to investigate color distribution in an image.'''
    def __init__(self,img):
        self.img = img
    
    def mapit(self, mode):
        # Find the centroid of the bounding box of the image (we know this by construction - testing the functions)
        w,h,c = self.img.shape
        outerEdge = np.array([(0,0), (0, h), (w,h), (w, 0)], dtype = np.int)
        M = cv2.moments(outerEdge)
        cX = int(M["m10"] / M["m00"])
        cY = int(M["m01"] / M["m00"])
        cv2.circle(self.img, (cX, cY), 7, (255, 255, 255), -1)
        cv2.putText(self.img, "center", (cX - 20, cY - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        cv2.rectangle(self.img, (cX-30, cY-30), (cY+30, cY+30),(0,255,0), 2)


    
class SquareLocator:
    def __init__(self, img, thumbnailDir = None):
        self.img = img
        self.squares = find_squares_V2(self.img, cos_limit = 0.2, show = True, info = True, destroy = False, thumbnailDir = thumbnailDir)
        square_contours = [square.contour for square in self.squares]
        cv2.drawContours( img, square_contours, -1, (0, 255, 0), 3 )

    def info(self):
        s = []
        s.append('Located %d squares within image')
        s.append('Each square is a contour from cv2.findContours')
        i = 0
        for sq in self.squares:
            i += 1
            s.append('Square %d : length = %d : area = %d' % (sq.ID, cv2.arcLength(sq.contour, True), sq.area))
        return '\n'.join(s)

class SquareLocatorV3:
    def __init__(self, img, thumbnailDir = None, mode = 1):
        self.img = img
        self.finder = SquareFinderV3(self.img, cos_limit = 0.2, show = True, info = True, destroy = False, thumbnailDir = thumbnailDir)
        self.squares = self.finder.find(mode)
        square_contours = [square.contour for square in self.squares]
        cv2.drawContours( img, square_contours, -1, (0, 255, 0), 3 )

    def info(self):
        s = []
        s.append('Located %d squares within image')
        s.append('Each square is a contour from cv2.findContours')
        i = 0
        for sq in self.squares:
            i += 1
            s.append('Square %d : length = %d : area = %d' % (sq.ID, cv2.arcLength(sq.contour, True), sq.area))
        return '\n'.join(s)

class SquaresOverlay:
    def __init__(self, img, squares, all = True):
        #w = ImageViewer(img)
        square_contours = [square.contour for square in squares]
        best_contours = []
        best_contour = classify_monitor_contour_set(square_contours)
        best_contours.append(best_contour.astype('int32'))
        print('Iterate over %d contours' % len(square_contours))
        if all:
            cycle = True
            while (cycle):
                for (i, c) in enumerate(square_contours):
                    src = img.copy()
                    cv2.drawContours( src, best_contours, -1, (0,0,255),3)
                    cv2.drawContours( src, square_contours, i, (0, 255, 0), 1 )
                    print('contour %d overlaid on basic image' % i)
                    cv2.imshow('view', src)
                    time.sleep(0.2)
                    k = cv2.waitKey(30) & 0xFF
                    if k == 27:
                        cycle = False
        else:
            cycle = True
            src = img.copy()
            while (cycle):
                cv2.drawContours( src, best_contours, -1, (0,0,255),3)
                cv2.imshow('view', src)
                time.sleep(0.2)
                k = cv2.waitKey(30) & 0xFF
                if k == 27:
                    cycle = False

        cv2.destroyWindow('view')

class SquaresOverlayV4:
    def __init__(self, img, squares, all = True):
        #w = ImageViewer(img)
        square_contours = [square.contour for square in squares]
        #pdb.set_trace()
        best_contours_tuples = classify_multi_monitors_contour_set(square_contours)
        best_contours = [contour.astype('int32') for (contour, index) in best_contours_tuples]
        #pdb.set_trace()
        #print('Iterate over %d contours' % len(square_contours))
        if all:
            cycle = True
            while (cycle):
                for (i, c) in enumerate(square_contours):
                    src = img.copy()
                    cv2.drawContours( src, square_contours, i, (0, 255, 0), 1 )
                    cv2.drawContours( src, best_contours, -1, (0,0,255),3)
                    print('contour %d overlaid on basic image' % i)
                    cv2.imshow('view', src)
                    time.sleep(0.2)
                    k = cv2.waitKey(30) & 0xFF
                    if k == 27:
                        cycle = False
        else:
            cycle = True
            src = img.copy()
            while (cycle):
                cv2.drawContours( src, best_contours, -1, (0,0,255),3)
                cv2.imshow('view', src)
                time.sleep(0.2)
                k = cv2.waitKey(30) & 0xFF
                if k == 27:
                    cycle = False

        cv2.destroyWindow('view')

#####################################################################################################################
# Contours and Sets of Contours : various problems in computer vision relevant to the project.
#
# All "Heuristics" functions have the same signature ; img, cnts, *args, **kwargs
#####################################################################################################################

def maxAreaHeuristic(img, cnts, *args, **kwargs):
    '''
    Concept  : Filter out unbelievable monitor contours based on area of monitor < 50% of image area.
    Critique : Can equally be achieved by sensible human cropping.   
    '''
    height = img.shape[0]
    width = img.shape[1]
    area = width*height
    max_area = int(0.5* area)
    filtered_contours = [c for c in cnts if c.area < max_area]
    return filtered_contours

def autoCropHeuristic(img, cnts, *args, **kwargs):
    '''
    Concept  : Auto crop to the boundary of the wall, or provide hooks for GUI assist.
    Critique : Can equally be achieved by sensible human cropping.   
    '''
    return cnts

def bezelIdentificationHeuristic(img, cnts, *args, **kwargs):
    '''
    Concept  : Bezels are characterised by nearly following the main monitor geometry, and especially have parallel qualities.
    Critique : Have seen edge cases where some bezels are found, others in the same image not.
    Related  : Nesting
    '''
    return cnts

def binaryContoursNestingFilterHeuristic(img, cnts, *args, **kwargs):
    '''
    Concept  : Use the found contours, with binary drawn contours to extract hierarchy and hence filter on nesting.
    Critique : WIP
    '''
    # Set the image to black (0): 
    img[:,:] = (0,0,0)
    # Draw all of the contours on the image in white
    contours = [c.contour for c in cnts]
    cv2.drawContours( img, contours, -1, (255, 255, 255), 1 )
    iv = ImageViewer(img)
    iv.windowShow()
    # Now extract any channel
    gray = cv2.split(img)[0]
    iv = ImageViewer(gray)
    iv.windowShow()
    retval, bin = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
    iv = ImageViewer(bin)
    iv.windowShow()
    # Now find the contours again, but this time we care about hierarchy (hence _TREE) - we get back next, previous, first_child, parent
    bin, contours, hierarchy = cv2.findContours(bin, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    iv = ImageViewer(bin)
    iv.windowShow()
    # Alternative flags : only take the external contours
    bin, contours, hierarchy = cv2.findContours(bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    iv = ImageViewer(bin)
    iv.windowShow()
    return cnts

def maxLinearDimensionHeuristic(img, cnts, *args, **kwargs):
    '''TODO: remove contours if they have a side that spans > 90% of the equivalent dimension.'''
    return cnts

def wallsWithParallelMonitorsHeuristic(img, cnts, *args, **kwargs):
    '''
    We expect that monitors are to be parallel.   Use the set of rectangles to find the statistically most likely fit based on parallel shapes.
    '''
    return cnts

def wallsWithEqualSizedMonitorsHeuristic(img, cnts, *args, **kwargs):
    '''
    We expect that monitors are to be parallel.   Use the set of rectangles to find the statistically most likely fit based on parallel shapes.
    '''
    return cnts

def cluedInByApproximateTiledGeometryHintHeuristic(img, cnts, *args, **kwargs):
    '''
    No issue for the human to say : I know the images are an array of n x m screens.
    '''
    return cnts

def filterContoursRemove(img, cnts, *args, **kwargs):
    f1 = maxAreaHeuristic(img, cnts)
    h = 'maxAreaHeuristic'
    print('Input %d : after %s reduced to %d' % (len(cnts), h, len(f1)))
#    f2 = anotherFineHeuristic(img, cnts)
#    h = 'anotherFineHeuristic'
#    print('Input %d : after %s reduced to %d' % (len(cnts), h, len(f2)))
    return f1

# TODO : expand the create_capture by providing a sequence of images as source.

class VideoSquareSearch:
    def __init__(self, video_src = 0, interactive = True, video = 'vss.avi', fallback = 'synth:bg=./data/hi.jpg:noise=0.05', save_frames = False, frame_dir = './data', frame_prefix='frame-'):
        cam = create_capture(video_src, fallback=fallback)
        vwriter = None
        if interactive:
            print("q to quit")
            window = 'video square search'
            cv2.namedWindow(window, cv2.WINDOW_NORMAL)
        else:
            vwriter = VideoWriter(video)
        run = True
        t = clock()
        frameCounter = 0
        while run:
            ret, img = cam.read()
            if interactive:
                print("read next image")
            squares = find_squares(img, 0.2)
            nOfSquares = len(squares)
            cv2.drawContours( img, squares, -1, (0, 255, 0), 3 )
            dt = clock() - t
            draw_str(img, (80, 80), 'time: %.1f ms found = %d' % (dt*1000, nOfSquares), 2.0)
            if interactive:
                cv2.imshow(window, img)    
                print('q to quit, n for next')
                ch = 0xff & cv2.waitKey(100) 
                if ch == ord('q'):
                    run = False
                elif ch == ord('n'):
                    continue
            else:
                vwriter.addFrame(img)
                if save_frames:
                    fn = os.path.join(frame_dir, '%s-%04d.%s' % (frame_prefix, frameCounter, 'jpg'))
                    print("Saving %d frame to %s" % (frameCounter, fn))
                    cv2.imwrite(fn, img)
                    frameCounter+=1
        if vwriter:
            vwriter.finalise()

class ChessboardDemo:
    def __init__(self, video_src = 0, 
                 interactive = True, 
                 video = 'chess.avi', fallback = 'synth:bg=./data/hi.jpg:noise=0.05', nFrames = 500):
        cam = create_capture(video_src, fallback=fallback)
        if not cam:
            print("Problem initialising cam")

        vwriter = VideoWriter(video)
        run = True
        t = clock()
        frameCounter = nFrames
        while frameCounter>0:
            ret, img = cam.read()
            vwriter.addFrame(img, width=1920)
            frameCounter-=1
            print("%d" % frameCounter)
        print("Created chessboard video : saved %d frames to %s" % (nFrames, video))
        vwriter.finalise()


#####################################################################################################################
# Tutorials
#####################################################################################################################

# Placeholder for snippets used in development taken from the tutorials.

class DemoFunctions:
    def __init__(self):
        pass
        
    def maskLogoOverImage(self):
        # Load two images
        img1 = cv2.imread('messi5.jpg')
        img2 = cv2.imread('opencv_logo.png')
        
        # I want to put logo on top-left corner, So I create a ROI
        rows,cols,channels = img2.shape
        roi = img1[0:rows, 0:cols ]
        
        # Now create a mask of logo and create its inverse mask also
        img2gray = cv2.cvtColor(img2,cv2.COLOR_BGR2GRAY)
        ret, mask = cv2.threshold(img2gray, 10, 255, cv2.THRESH_BINARY)
        mask_inv = cv2.bitwise_not(mask)
        
        # Now black-out the area of logo in ROI
        img1_bg = cv2.bitwise_and(roi,roi,mask = mask_inv)
    
        # Take only region of logo from logo image.
        img2_fg = cv2.bitwise_and(img2,img2,mask = mask)
        
        # Put logo in ROI and modify the main image
        dst = cv2.add(img1_bg,img2_fg)
        img1[0:rows, 0:cols ] = dst
        
        cv2.imshow('res',img1)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


#####################################################################################################################
# Prototypes & Convenient CLI/GUI Dispatcher to rebuild mental picture of where we are/repeat on new platforms.
#####################################################################################################################

def vssProto():
    '''
    Demonstrate basic application of the SquareLocator and generate a video with overlays 
    of the located squares from a video source.
    Last run from 3XS Mint18 : seems to take for ever based on rotating_wall.mp4 video.
    Unable to find the original reference data.
    Uploaded to YouTube from somewhere : see
    '''
    vss = VideoSquareSearch('./data/rotating_wall.mp4', False, 'piwall-search-mono.avi')

def albumProto():
    '''Demonstrate the extended VideoSynthBase class Album which takes a set of images.'''
    bufFnsAsCsv = ",".join(glob.glob('./data/2x2-*.jpg'))
    album = 'synth:class=album:noise=0.0:bg=./data/2x2-red-1.jpg:size=1920x1080:album=%s' % bufFnsAsCsv
    vss = VideoSquareSearch(video_src = 0, interactive = False, video = "album.avi", fallback = album, save_frames = True)

def chessboardProto():
    '''Create an HD movie for testing the tile geometry functions.'''
    chess = 'synth:class=chess:bg=./data/2x2-red-1.jpg:noise=0.1:size=1920x1080'
    chess = 'synth:class=testcard:noise=0.1:size=1920x1080'
    vss = ChessboardDemo(video_src = 0, interactive = False, video = "chess.avi", fallback = chess)

def hdsbProto():
    '''Generate HD solid colour blocks for use in injecting known patterns.'''
    hdSolidBlock()
    hdSolidBlock('blueHDSolidBlock.jpg', [255,0,0])
    hdSolidBlock('greenHDSolidBlock.jpg', [0,255,0])
    hdSolidBlock('redHDSolidBlock.jpg', [0,0,255])
    hdSolidBlock('whiteHDSolidBlock.jpg', [255,255,255])
    hdSolidBlock('blackHDSolidBlock.jpg', [0,0,0])
    hdSolidBlock('cyanHDSolidBlock.jpg', [255,255,0])
    hdSolidBlock('yellowHDSolidBlock.jpg', [0,255,255])
    
def ivsqlProto():
    '''Demonstrate use of the SquareLocator and ImageViewer classes.'''
    for fn in glob('./data/hi.jpg'):
        vw = ImageViewer(fn)
        sl = SquareLocator(vw.img)
        print(sl.info())
        vw.windowShow()

def ivsqlRedProto():
    '''Demonstrate use of the SquareLocator and ImageViewer classes.'''
    for fn in glob.glob('./data/2x2-*.jpg'):
        stem = os.path.splitext(os.path.basename(fn))[0]
        vw = ImageViewer(fn)
        sl = SquareLocator(vw.img, thumbnailDir = stem)
        print(sl.info())
        vw.windowShow()

def ivsqlRedProtoV3(mode):
    '''Demonstrate use of the SquareLocator and ImageViewer classes.'''
    fn = './data/2x2-red-1.jpg'
    stem = os.path.splitext(os.path.basename(fn))[0]
    vw = ImageViewer(fn)
    sl = SquareLocatorV3(vw.img, thumbnailDir = stem, mode = mode)
    print(sl.info())
    vw.windowShow()

class IPlog:
    def __init__(self, logfile = 'opencv_piwall_progress.log'):
        self.logfile = logfile
        self.fh = open(self.logfile, 'a')
    def comment(self, msg):
        if type(msg) == type(''):
            self.fh.writelines('%s\n' % msg)
        else:
            lines = '%s' % msg
            newlines = []
            for l in lines.split('\n'):
                newlines.append('\t%s' % l)
            self.fh.writelines('\n'.join(newlines))
        print('%s' % msg)
    def close(self):
        # How to do with IPlog.... and trigger close automatically ?
        self.fh.close()

def denoise_foreground(img, fgmask):
    img_bw = 255*(fgmask > 5).astype('uint8')
    se1 = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5))
    se2 = cv2.getStructuringElement(cv2.MORPH_RECT, (2,2))
    mask = cv2.morphologyEx(img_bw, cv2.MORPH_CLOSE, se1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, se2)
    mask = np.dstack([mask, mask, mask]) / 255
    img_dn = img * mask
    return img_dn

def sfv3Proto(mode = None, imgPath = None):
    '''
    Iterate through the deconstructed image processing options in SquareFinderV3 (sfv3).
    '''
    if not mode:
        mode = 1
    if not imgPath:
        imgPath = './data/2x2-red-1.jpg'
    img = cv2.imread(imgPath)
    sfv3 = SquareFinderV3(img, cos_limit = 0.5)
    squares = sfv3.find(mode)
    SquaresOverlay(img, squares)
    # Heuristic when guided by MOG removal to find only contours close to the monitor to get average
    best_contours = []
    best_contour = classify_monitor_contour_set(square_contours)
    best_contours.append(best_contour.astype('int32'))
    # Best contour may be angled if the camera is not well lined up
    # Find a transformation to map the image data to rectilinear/oriented normal to standard wall axes
    log = IPlog()
    log.comment('SquareFinderV3 acting on %s finds %d squares' % (imgPath, len(squares)))
    log.comment(sfv3)
    log.close()

class PiwallImageSeries:
    '''Process a series of images of piwalls in which transitions are engineered to highlight the tiles.'''
    def __init__(self, globPattern, mode = 4, transition_threshold = 0.8):
        self.globPattern = globPattern
        self.mode = mode
        self.transition_threshold = transition_threshold
        self.frame_files = glob.glob(self.globPattern)
        self.frame_files.sort()
        self.frames = [cv2.imread(f) for f in self.frame_files]
        self.transitions = []

    def subtract_background(self):
        fgbg = cv2.createBackgroundSubtractorMOG2()
        prev = self.frames[0]
        fgmask = fgbg.apply(prev)
        for (i,next) in enumerate(self.frames[1:]):
            prev_gray = cv2.cvtColor(prev, cv2.COLOR_BGR2GRAY)
            next_gray = cv2.cvtColor(next, cv2.COLOR_BGR2GRAY)
            similarity_metric = compare_ssim(prev_gray, next_gray)
            print('prev/next similarity measure = %f' % similarity_metric)
            if similarity_metric < self.transition_threshold:
                fgmask = fgbg.apply(next)
                fgdn = denoise_foreground(next, fgmask)
                self.transitions.append((1, fgdn))
            else:
                fgmask = fgbg.apply(next)
                self.transitions.append((0, None))
            prev = next.copy()

    def locate(self, all = False, show = False, outimg = None):
        for (transition, mask) in self.transitions:
            if transition == 1:
                sfv3 = SquareFinderV3(mask, cos_limit = 0.5)
                squares = sfv3.find(self.mode)
                if show:
                    SquaresOverlayV4(mask, squares, all = all)
                    SquaresOverlayV4(mask, squares, all = False)
                else:
                    square_contours = [square.contour for square in squares]
                    best_contours_tuples = classify_multi_monitors_contour_set(square_contours)
                    found = mask.copy()
                    self.best_contours = [contour.astype('int32') for (contour, index) in best_contours_tuples]
                    cv2.drawContours( found, self.best_contours, -1, (0,0,255),3)
                    if outimg:
                        cv2.imwrite(outimg, found)
                return self.best_contours

    def as_wall(self, filename):
        (h, w, c) = self.frames[0].shape
        self.wall = Wall(w, h)
        for bc in self.best_contours:
            tlx,tly = bc[0]
            brx,bry = bc[2]
            w = brx - tlx
            h = bry - tly
            self.wall.add_tile(Tile(w, h), tlx, tly)
        if filename:
            self.wall.save(filename)

    def __repr__(self):
        s = []
        s.append('%d frames considered' % len(self.frames))
        ntrans = 0
        for (t,m) in self.transitions:
            if t == 1:
                 ntrans += 1
        s.append('%d transitions identified' % ntrans)
        return '\n'.join(s)

def sfv4Proto(globPattern, mode = None, outimg = None, wallfn = None):
    pwis = PiwallImageSeries(globPattern, mode = mode)
    pwis.subtract_background()
    best_contours = pwis.locate(all = True, outimg = outimg)
    pwis.as_wall('v4wall.pickle')
    pdb.set_trace()
                            
#####################################################################################################################
# GetOpts Front End
#####################################################################################################################

import getopt
import sys

def usage():
    print('''
    piwall.py 
     --vssdemo|-v rotating    : iterate the VideoSquareSearch over rotating video, and output located data in piwall-search-mono.avi
     --vssdemo|-v album       : iterate the VideoSquareSearch over sequence of images, and output located data in album.avi
     --sfv3mode|-s [mode 1-3] : run the SquareLocatorV3 algorithm : set the mode 1-3     < default image 2x2-red-1.jpg >
                               : 1 => call gaussianBlur(); cannyThresholding()
                               : 2 => call gimpMarkup()
                               : 3 => call gaussianBlur(); colourMapping(); solidRedFilter(); [#cannyThresholding]
                               : 4 => as 1, but with cv2.RETR_EXTERNAL as contour_retrieval_mode
                               : 5 => as 1, but with cv2.RETR_TREE as contour_retrieval_mode, then filter only outermost contours
                               : 6 => new model which takes a series of images which have transitions that identify the monitors.
     --sfv3img|-i [image path]: run the SquareFinderV3 algorithm  : set the input image  < default mode 1>
     --sfv4glob|-g [image glob pattern] : set the series of input images to be pattern-[%03d].jpg
    ''')

def main():
    vssopt = None
    sfv3mode = None
    sfv3img = None
    sfv4glob = None
    outimg = None
    
    options, remainder = getopt.gnu_getopt(sys.argv[1:],
                                       'i:o:s:g:v:h',
                                       ['help', 'sfv3img=', 'sfv3mode=', 'vssdemo=', 'sfv4glob=', 'outimg='])
    for opt, arg in options:
        if opt in ('-h', '--help'):
            usage()
        elif opt in ('-v', '--vssdemo'):
            vssopt = arg
        elif opt in ('-s', '--sfv3mode'):
            sfv3mode = int(arg)
        elif opt in ('-i', '--sfv3img'):
            sfv3img = arg
        elif opt in ('-o', '--outimg'):
            outimg = arg
        elif opt in ('-g', '--sfv4glob'):
            sfv4glob = arg
        elif opt in ('-h', '--help'):
            usage()
            sys.exit(0)
        else:
            pass

    # Hook to run vssopt
    if vssopt:
        print('Running VSS')
        if vssopt == 'rotating':
            t_start = time.time()
            vssProto()
            t_end = time.time()
            print('vss rotating : %d seconds' % (t_end - t_start))
        elif vssopt == 'album':
            albumProto()
    else:
        print("Skipping VSS demo.")

    # Hook to run sfv3 or sfv4
    if sfv3img:
        print('Running SFV3 : %d %s %s' % (sfv3mode, sfv3img, sfv3glob))
        sfv3Proto(sfv3mode, sfv3img)
    elif sfv4glob:
        sfv4Proto(sfv4glob, sfv3mode, outimg)
    else:
        print("Skipping sfv3 demo.")

    print("That's all folks...")

#####################################################################################################################
# Main
#####################################################################################################################

# DONE : add a neat repr method to SFV3 to explain progress and status.

# TODO : add auto git log to track progress and rebuild momentum [WIBNI]
# TODO : give information as to the distribution of the "squares" found
# TODO : are any of the squares wholly nested ? intersecting ?

# HEURISTICS : Approximate size and number of squares can be fed in as an estimator, but
#            : Unless wall comprises only one monitor (useless case) : max area at least image area / 2

if __name__ == '__main__':
    main()
    sys.exit(0)
    chessboardProto()
    ivsqlRedProtoV3(2)
    sys.exit(0)
    albumProto()
    usage()
