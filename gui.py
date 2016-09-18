# import the necessary packages
import argparse
from model import *
from Tkinter import *
import numpy as np
import cv2

refPt = []
image = np.zeros((600, 600, 3), dtype = "uint8")
clone = image.copy()

wall = Wall(600, 600, None, "testWall")
testTile = Tile(50, 50)
wall.add_tile(testTile, 0,0)
wall.draw(image)

selectedTile = None
updatedTile = None
tile_form = None
tiles = []

def click_and_crop(event, x, y, flags, param):
    global refPt, image, tiles, wall, selectedTile
    if event == cv2.EVENT_LBUTTONDOWN:
        refPt = [(x, y)]
    elif event == cv2.EVENT_LBUTTONUP:
        newTile = Tile(abs(refPt[0][0] - x), abs(refPt[0][1] - y))
        selectedTile = newTile
        wall.add_tile(newTile, min(refPt[0][0], x), min(refPt[0][1], y))
        wall.draw(image)

    elif event == cv2.EVENT_RBUTTONUP:
        tile_popup()


def tile_popup():
    global tile_form, updatedTile
    tile_form = Tk()
    tile_form.wm_title(selectedTile.name)
    updatedTile = selectedTile.copy()

    Label(tile_form, text="Wall: ").grid(row=0, column=0)
    Label(tile_form, text=selectedTile.wall.desc).grid(row=0, column=1)
    Label(tile_form, text="Width").grid(row=1, column=0)
    Label(tile_form, text="Height").grid(row=2, column=0)
    Label(tile_form, text="xPos").grid(row=3, column=0)
    Label(tile_form, text="yPos").grid(row=4, column=0)
    Label(tile_form, text="BezelL").grid(row=5, column=0)
    Label(tile_form, text="BezelT").grid(row=6, column=0)
    Label(tile_form, text="BezelR").grid(row=7, column=0)
    Label(tile_form, text="BezelB").grid(row=8, column=0)
    Button(tile_form, text="Save", command= saveClicked).grid(row=9, column=0)
    Button(tile_form, text="Cancel", command= cancelClicked).grid(row=9, column=1)


    #Width
    width_entry = Entry(tile_form, bd =5)
    width_entry.insert(0, selectedTile.W())
    width_entry.grid(row=1, column =1)

    #Height
    height_entry = Entry(tile_form, bd =5)
    height_entry.grid(row=2, column =1)
    height_entry.insert(0, selectedTile.H())

    #xPos
    xPos_entry = Entry(tile_form, bd =5)
    xPos_entry.grid(row=3, column =1)
    xPos_entry.insert(0, selectedTile.wx)

    #yPos
    yPos_entry = Entry(tile_form, bd =5)
    yPos_entry.grid(row=4, column =1)
    yPos_entry.insert(0, selectedTile.wy)

    #BezelL
    bezelL_entry = Entry(tile_form, bd =5)
    bezelL_entry.grid(row=5, column =1)
    bezelL_entry.insert(0, selectedTile.l)

    #BezelT
    bezelT_entry = Entry(tile_form, bd =5)
    bezelT_entry.grid(row=6, column =1)
    bezelT_entry.insert(0, selectedTile.t)

    #BezelR
    bezelR_entry = Entry(tile_form, bd =5)
    bezelR_entry.grid(row=7, column =1)
    bezelR_entry.insert(0, selectedTile.r)

    #BezelB
    bezelT_entry = Entry(tile_form, bd =5)
    bezelT_entry.grid(row=8, column =1)
    bezelT_entry.insert(0, selectedTile.b)

    tile_form.mainloop()

def saveClicked():
    global tile_form
    print("Values saved")
    tile_form.destroy()

def cancelClicked():
    global tile_form
    print("Values not saved")
    tile_form.destroy()

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
