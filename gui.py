#!/usr/bin/env python

'''
Usage:
    python gui.py

    Click and drag on the canvas the size of the  tile (if the tile is smaller than 100 sqpixel it will not be drawn)
    Right click on a tile will allow you to edit the attributes of it

    Key bindings:
        g - generates the .piwall file with the name generatedpiwall

    19/09/2016 - 10 minutes - implemented saving the piwall file
    18/09/2016 - 3 hours
'''

import argparse
from model import *
from Tkinter import *
from dotpiwall import DotPiwall
import numpy as np
import cv2

refPt = []
image = np.zeros((600, 600, 3), dtype = "uint8")
clone = image.copy()

wall = Wall(600, 600, None, "testWall")

selectedTile = None
updatedTile = None
tile_form = None
tiles = []

generated_piwall = "generatedpiwall"

def click_and_crop(event, x, y, flags, param):
    global refPt, image, tiles, wall, selectedTile
    if event == cv2.EVENT_LBUTTONDOWN:
        refPt = [(x, y)]
    elif event == cv2.EVENT_LBUTTONUP:
        #Restrict to create tiles that are at least 100 sqpixel big
        if (abs(refPt[0][0] - x) * abs(refPt[0][1] - y) >= 100):
            newTile = Tile(abs(refPt[0][0] - x), abs(refPt[0][1] - y))
            wall.add_tile(newTile, min(refPt[0][0], x), min(refPt[0][1], y))
            wall.draw(image)
            tiles.append(newTile)

    elif event == cv2.EVENT_RBUTTONUP:
        found = False
        iterator = 0
        while not found and iterator < len(tiles):
            if tiles[iterator].containsCoordinate((x,y)):
                found = True
                selectedTile = tiles[iterator]
                tile_popup()
            iterator = iterator+1

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
    Button(tile_form, text="Delete", command= deleteClicked).grid(row=9, column=1)
    Button(tile_form, text="Cancel", command= cancelClicked).grid(row=9, column=2)


    #Width
    width_entry = Entry(tile_form, bd =5)
    width_entry.insert(0, selectedTile.w)
    width_entry.grid(row=1, column =1)

    #Height
    height_entry = Entry(tile_form, bd =5)
    height_entry.grid(row=2, column =1)
    height_entry.insert(0, selectedTile.h)

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
    bezelB_entry = Entry(tile_form, bd =5)
    bezelB_entry.grid(row=8, column =1)
    bezelB_entry.insert(0, selectedTile.b)

    tile_form.entries = [width_entry, height_entry, xPos_entry, yPos_entry, bezelL_entry,
                         bezelT_entry, bezelR_entry, bezelB_entry]

    tile_form.mainloop()

def saveClicked():
    global tile_form, selectedTile, image, wall
    print("Values saved")
    selectedTile.w = int(tile_form.entries[0].get())
    selectedTile.h = int(tile_form.entries[1].get())
    selectedTile.wx = int(tile_form.entries[2].get())
    selectedTile.wy = int(tile_form.entries[3].get())
    selectedTile.l = int(tile_form.entries[4].get())
    selectedTile.t = int(tile_form.entries[5].get())
    selectedTile.r = int(tile_form.entries[6].get())
    selectedTile.b = int(tile_form.entries[7].get())
    image = clone.copy()
    wall.draw(image)
    tile_form.destroy()


def cancelClicked():
    global tile_form
    print("Values not saved")
    tile_form.destroy()

def deleteClicked():
    global tile_form, wall, selectedTile, image
    print("Tile removed")
    wall.remove_tile(selectedTile)
    tiles.remove(selectedTile)
    image = clone.copy()
    wall.draw(image)
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

    elif key == ord("g"):
        print("savig the .piwall file")
        target = open(generated_piwall, 'w')
        dotpiwall = DotPiwall("test", wall)
        #print(str(dotpiwall))
        target.write(str(dotpiwall))
        target.close()

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
