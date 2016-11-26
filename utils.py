#!/usr/bin/env python

'''
#####################################################################################################################
# Helper Classes for opencv piwall tools.
#####################################################################################################################
'''
from itertools import count

# TODO: rewrite in true iterator idiom style.
class FilenameSequence:
    def __init__(self, prefix, suffix):
        self.prefix = prefix
        self.suffix = suffix
        self.id = count(0)
    
    def next(self, tag = None):
        if tag:
            return '%s-%s_%04d.%s' % (self.prefix, tag, self.id.next(), self.suffix)
        else:
            return '%s_%04d.%s' % (self.prefix, self.id.next(), self.suffix)

class ImageViewer:
    '''Very simple wrapper to display images and add key options to show information.'''
    def __init__(self, img = './data/hi.jpg'):
        if type(img) == type(''):
            if os.path.exists(img):
                self.path = img
                self.img = cv2.imread(self.path)
            else:
                print("No such image found at %s" % img)
                return
        else:
            self.path = "No path - image supplied directly"
            self.img = img
        shape = self.img.shape
        h = shape[0]
        w = shape[1]
        self.aspectRatio = float(w)/float(h)

    def show(self, waitKey = 'n', window = 'Pi Wall', destroy = True, info = False, w = 500, thumbnailfn = None):
        '''
        thumbnailfn : filename into which to save a resized copy
        '''
        print('Display %s.\n\tPress %s to exit viewer' % (self.path, waitKey))
        cv2.namedWindow(window, cv2.WINDOW_NORMAL)
        cv2.imshow(window, self.img)
        h = int(w/self.aspectRatio)
        cv2.resizeWindow(window, w, h)
        if thumbnailfn:
            thumb = self.img.copy()
            # Or cv2.copyMakeBorder(img, 0,0,0,0,cv2.BORDER_REPLICATE)
            thumb = cv2.resize(thumb, (w,h))
            cv2.imwrite(thumbnailfn, thumb)
        if info: self.imageInfo()
        if destroy:
            run = True
            while run:
                ch = 0xff & cv2.waitKey()
                if ch == ord('%s' % waitKey):
                    print('%s pressed. exiting' % waitKey)
                    run = False
                elif ch == ord('i'):
                    self.imageInfo()
                else:
                    print('invalid command %s' % chr(ch))
            cv2.destroyWindow(window)

    def windowShow(self, waitKey = 'n'):
        cv2.namedWindow('wall', cv2.WINDOW_NORMAL)
        self.show(waitKey, 'wall')
    
    def imageInfo(self):
        print('image.size is %d' % self.img.size)
        print('image.shape is {0}'.format(self.img.shape))
        print('image.dtype is %s' % str(self.img.dtype))    

def main():
    pass

if __name__ == '__main__':
    main()
