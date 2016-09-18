# import the necessary packages
import argparse
from model import Wall
from model import Tile
import Tkinter
import numpy as np
import cv2

# initialize the list of reference points and boolean indicating
# whether cropping is being performed or not
refPt = []

# construct the argument parser and parse the arguments
#ap = argparse.ArgumentParser()
#ap.add_argument("-i", "--image", required=True, help="Path to the image")
#args = vars(ap.parse_args())

# load the image, clone it, and setup the mouse callback function
image = np.zeros((600, 600, 3), dtype = "uint8")
clone = image.copy()

wall = Wall(100, 100)
tiles = []


def click_and_crop(event, x, y, flags, param):
    global refPt, image, tiles
    if event == cv2.EVENT_LBUTTONDOWN:
        refPt = [(x, y)]
    elif event == cv2.EVENT_LBUTTONUP:
        newTile = Tile(abs(refPt[0][0] - x), abs(refPt[0][1] - y))
        wall.add_tile(newTile, min(refPt[0][0], x), min(refPt[0][1], y))

        top = Tkinter.Tk()
        # Code to add widgets will go here...
        top.mainloop()

    elif event == cv2.EVENT_RBUTTONUP:
        image = clone.copy()


cv2.namedWindow("image")
cv2.setMouseCallback("image", click_and_crop)

# keep looping until the 'q' key is pressed
while True:
    # display the image and wait for a keypress
    cv2.imshow("image", image)
    key = cv2.waitKey(1) & 0xFF

    # if the 'r' key is pressed, reset the cropping region
    if key == ord("r"):
        image = clone.copy()

    # if the 'c' key is pressed, break from the loop
    elif key == ord("c"):
        break

# if there are two reference points, then crop the region of interest
# from teh image and display it
if len(refPt) == 2:
    roi = clone[refPt[0][1]:refPt[1][1], refPt[0][0]:refPt[1][0]]
    cv2.imshow("ROI", roi)
    cv2.waitKey(0)

# close all open windows
cv2.destroyAllWindows()
