
'''
Requires http://docs.opencv.org/trunk/d7/dfc/group__highgui.html module.  
cv2.cv  However, in OpenCV 3.0.0 this is renamed as highgui

Recompiled with OpenCV 3.1.0.  Porting this example needs to use some renaming.
See http://www.pyimagesearch.com/2015/03/09/capturing-mouse-click-events-with-python-and-opencv/

# ------------------------------------------------------------- ------------------------------------------------------------
# WAS                                                          : NOW
# ------------------------------------------------------------- ------------------------------------------------------------
cv2.CV_EVENT_LBUTTONDOWN                                       : cv2.EVENT_LBUTTONDOWN
cv2.SetMouseCallback('real image', on_mouse, 0)                : cv2.setMouseCallback('real image', on_mouse, 0)               
'''

import cv2

# WAS import cv2.cv as cv
# Fails on 3.0.0
# REF incorrect answer on stackflow : http://stackoverflow.com/questions/13491253/no-highgui-in-python  Says dropped after 2.3.1
#
# See also http://docs.opencv.org/trunk/db/d5b/tutorial_py_mouse_handling.html
# Simpler answer : functionality may have been merged into cv2.
# Or at least is present in 3.1.0-dev !!!
#
#
#import cv2.highgui as cv
#
#
# NEXT exercise : get opencv-3.1.0 in anaconda (using the environment stuff)
# Also follow through : http://docs.opencv.org/3.0-beta/doc/py_tutorials/py_bindings/py_bindings_basics/py_bindings_basics.html#bindings-basics
#
# Also do some basic C++ OpenCV to open up the possibilities.
#
# Start storyboarding some of my concepts to open up interaction with Zsolt.
#
# Use KanbanFlow

import sys
from time import time
boxes = []

def on_mouse(event, x, y, flags, params):
    # global img
    t = time()
    
    if event == cv2.EVENT_LBUTTONDOWN:
        print 'Start Mouse Position: '+str(x)+', '+str(y)
        sbox = [x, y]
        boxes.append(sbox)
             # print count
             # print sbox
             
    elif event == cv2.EVENT_LBUTTONUP:
        print 'End Mouse Position: '+str(x)+', '+str(y)
        ebox = [x, y]
        boxes.append(ebox)
        print boxes
        crop = img[boxes[-2][1]:boxes[-1][1],boxes[-2][0]:boxes[-1][0]]

        cv2.imshow('crop',crop)
        k =  cv2.waitKey(0)
        if ord('r')== k:
            cv2.imwrite('Crop'+str(t)+'.jpg',crop)
            print "Written to file"

if __name__ == '__main__':
    if len(sys.argv) > 1:
        imgpath = sys.argv[1]
    else:
        imgpath = '../data/beach-2x2-hd.png'
    
    count = 0
    while(1):
        count += 1
        img = cv2.imread(imgpath,0)
        # img = cv2.blur(img, (3,3))
        img = cv2.resize(img, None, fx = 0.25,fy = 0.25)
        
        cv2.namedWindow('real image')
        cv2.setMouseCallback('real image', on_mouse, 0)
        cv2.imshow('real image', img)
        if count < 50:
            if cv2.waitKey(33) == 27:
                cv2.destroyAllWindows()
                break
            elif count >= 50:
                if cv2.waitKey(0) == 27:
                    cv2.destroyAllWindows()
                    break
                count = 0
