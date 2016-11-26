#!/usr/bin/env python

'''
Usage:
    python gui.py

    Click and drag on the canvas the size of the  tile (if the tile is smaller than 100 sqpixel it will not be drawn)
    Right click on a tile will allow you to edit the attributes of it

    Key bindings:
        g - generates the .piwall file with the name generatedpiwall
        d - togle between move/draw tiles

    19/09/2016 18:50 - 19:30 - implemented dragging the tiles
    19/09/2016 - 10 minutes - implemented saving the piwall file
    18/09/2016 - 3 hours - initial interface
'''

import pdb
import argparse
from model import *
from Tkinter import *
from dotpiwall import DotPiwall
import numpy as np
import cv2
from functools import partial
import sys

MINIMUM_RESIZE_WIDTH = 10

refPt = []

wall = Wall(600, 600, None, "testWall")

selected_tile = None
updated_tile = None
tile_form = None
tiles = []
draw_tile = True

# tile dragging helpers
l_mouse_button_down = False
mouse_over_tile = False
offsets = (0,0)

generated_piwall = "generatedpiwall"

def mouse_callback(event, x, y, flags, param):
    global refPt, image, tiles, wall, selected_tile, l_mouse_button_down, mouse_over_tile,\
        clone, offsets

    if event == cv2.EVENT_LBUTTONDOWN:
        l_mouse_button_down = True
        refPt = [(x, y)]
        if not draw_tile:
            if find_hovered_tile(x,y):
                mouse_over_tile = True
                offsets = (x - selected_tile.wx - selected_tile.l, y-selected_tile.wy - selected_tile.t)
            else:
                mouse_over_tile = False

    elif event == cv2.EVENT_LBUTTONUP:
        l_mouse_button_down = False
        if draw_tile:
            #Restrict to create tiles that are at least 100 sqpixel big
            if (abs(refPt[0][0] - x) * abs(refPt[0][1] - y) >= 100):
                newTile = Tile(abs(refPt[0][0] - x), abs(refPt[0][1] - y))
                wall.add_tile(newTile, min(refPt[0][0], x), min(refPt[0][1], y))
                wall.draw(image)
                tiles.append(newTile)
        else:
            print("dragging the tile")

    elif event == cv2.EVENT_RBUTTONUP:
        if find_hovered_tile(x,y):
            tile_popup()

    elif event == cv2.EVENT_MOUSEMOVE:
        # TODO: Implement the t r b resize too
        if l_mouse_button_down and mouse_over_tile and x >= selected_tile.wx and x <= selected_tile.wx + 5:
            new_w = selected_tile.w + selected_tile.wx + selected_tile.l - x
            # TODO: Fix when the bezel is resized to the left
            print(
            "selected_tile.w = {} selected_tile.wx = {} x = {} new_w = {}".format(selected_tile.w, selected_tile.wx, x,
                                                                                  new_w))
            if new_w >= MINIMUM_RESIZE_WIDTH:
                selected_tile.w = new_w
                selected_tile.wx = x - selected_tile.l
                image = clone.copy()
                wall.draw(image)
                print("RESIZING")
        elif l_mouse_button_down and mouse_over_tile and not draw_tile:
            selected_tile.wx = x - offsets[0]
            selected_tile.wy = y - offsets[1]
            image = clone.copy()
            wall.draw(image)
        #TODO: Implement an else that will start drawing the tile while in the draw mode


def find_hovered_tile(x,y):
    global selected_tile
    found = False
    iterator = 0
    while not found and iterator < len(tiles):
        if tiles[iterator].containsCoordinate((x, y)):
            found = True
            selected_tile = tiles[iterator]
        iterator += 1
    return found


def tile_popup():
    global tile_form, updated_tile
    tile_form = Tk()
    tile_form.wm_title(selected_tile.name)
    updated_tile = selected_tile.copy()

    Label(tile_form, text="Wall: ").grid(row=0, column=0)
    Label(tile_form, text=selected_tile.wall.desc).grid(row=0, column=1)
    Label(tile_form, text="Width").grid(row=1, column=0)
    Label(tile_form, text="Height").grid(row=2, column=0)
    Label(tile_form, text="xPos").grid(row=3, column=0)
    Label(tile_form, text="yPos").grid(row=4, column=0)
    Label(tile_form, text="BezelL").grid(row=5, column=0)
    Label(tile_form, text="BezelT").grid(row=6, column=0)
    Label(tile_form, text="BezelR").grid(row=7, column=0)
    Label(tile_form, text="BezelB").grid(row=8, column=0)
    Button(tile_form, text="Save", command= save_clicked).grid(row=9, column=0)
    Button(tile_form, text="Delete", command= delete_clicked).grid(row=9, column=1)
    Button(tile_form, text="Cancel", command= cancel_clicked).grid(row=9, column=2)

    # Width
    width_entry = Entry(tile_form, bd =5)
    width_entry.insert(0, selected_tile.w)
    width_entry.grid(row=1, column =1)

    # Height
    height_entry = Entry(tile_form, bd =5)
    height_entry.grid(row=2, column =1)
    height_entry.insert(0, selected_tile.h)

    # xPos
    xPos_entry = Entry(tile_form, bd =5)
    xPos_entry.grid(row=3, column =1)
    xPos_entry.insert(0, selected_tile.wx)

    # yPos
    yPos_entry = Entry(tile_form, bd =5)
    yPos_entry.grid(row=4, column =1)
    yPos_entry.insert(0, selected_tile.wy)

    # BezelL
    bezelL_entry = Entry(tile_form, bd =5)
    bezelL_entry.grid(row=5, column =1)
    bezelL_entry.insert(0, selected_tile.l)

    # BezelT
    bezelT_entry = Entry(tile_form, bd =5)
    bezelT_entry.grid(row=6, column =1)
    bezelT_entry.insert(0, selected_tile.t)

    # BezelR
    bezelR_entry = Entry(tile_form, bd =5)
    bezelR_entry.grid(row=7, column =1)
    bezelR_entry.insert(0, selected_tile.r)

    # BezelB
    bezelB_entry = Entry(tile_form, bd =5)
    bezelB_entry.grid(row=8, column =1)
    bezelB_entry.insert(0, selected_tile.b)

    tile_form.entries = [width_entry, height_entry, xPos_entry, yPos_entry, bezelL_entry,
                         bezelT_entry, bezelR_entry, bezelB_entry]

    tile_form.mainloop()

def help_popup():
    global help_form
    help_form = Tk()
    help_form.wm_title('Help')

    _row = 0
    Label(help_form, text="Quit: 'q|c' ").grid(row=_row, column=0)
    _row += 1
    Label(help_form, text="Generate .piwall 'g'").grid(row=_row, column=0)
    _row += 1
    Label(help_form, text="Save wall 's'").grid(row=_row, column=0)
    _row += 1
    Label(help_form, text="Toggle draw/move 'd'").grid(row=_row, column=0)
    _row += 1
    Button(help_form, text="Quit (or press Escape or 'q')", command=help_form.destroy).grid(row=_row, column=0)
    _row += 1

    # Ref Tk-HOWTO bind function to raw widget inline http://stackoverflow.com/questions/7299955/tkinter-binding-a-function-with-arguments-to-a-widget

    help_form.bind("q", partial(lambda event:help_form.destroy()))
    help_form.bind("<Escape>", partial(lambda event:help_form.destroy()))
    
    help_form.mainloop()
    
def save_wall_popup():
    global save_wall_form, updated_tile, wall_save_file, wall
    save_wall_form = Tk()
    wall_save_file = 'wall.pickle'
    save_wall_form.wm_title('save wall')

    Label(save_wall_form, text="Save Wall").grid(row=0, column=0)
    Label(save_wall_form, text="Wall Save File").grid(row=1, column=0)
    Button(save_wall_form, text="Save", command=save_wall).grid(row=9, column=0)
    Button(save_wall_form, text="Cancel", command=save_wall_form.destroy).grid(row=9, column=1)

    # Filename
    filename_entry = Entry(save_wall_form, bd =5)
    filename_entry.insert(0, wall_save_file)
    filename_entry.grid(row=1, column =1)

    save_wall_form.entries = [filename_entry]

    save_wall_form.mainloop()

def save_wall():
    global save_wall_form, wall_save_file, wall
    wall_save_file = save_wall_form.entries[0].get()
    print('Save wall %s to %s' % (wall, wall_save_file))
    with open(wall_save_file, 'w') as fh:
        pickle.dump(wall, fh)
    print('saved wall to %s' % wall_save_file)
    save_wall_form.destroy()

def load_wall_popup():
    global load_wall_form, wall_save_file, wall
    load_wall_form = Tk()
    wall_save_file = 'wall.pickle'
    load_wall_form.wm_title('load wall')

    Label(load_wall_form, text="Load Wall").grid(row=0, column=0)
    Label(load_wall_form, text="Wall Save File").grid(row=1, column=0)
    Button(load_wall_form, text="Load", command=load_wall).grid(row=9, column=0)
    Button(load_wall_form, text="Cancel", command=load_wall_form.destroy).grid(row=9, column=1)

    # Filename
    filename_entry = Entry(load_wall_form, bd =5)
    filename_entry.insert(0, wall_save_file)
    filename_entry.grid(row=1, column =1)

    load_wall_form.entries = [filename_entry]

    load_wall_form.mainloop()
        
def load_wall():
    global load_wall_form, wall_save_file, wall
    wall_save_file = load_wall_form.entries[0].get()
    _load_wall(wall_save_file)
    load_wall_form.destroy()

def _load_wall(save_file):
    global wall, tiles
    print('Load wall from %s' % save_file)
    with open(save_file, 'r') as fh:
        wall = pickle.load(fh)
    for t in wall.tilesByOrder:
        tiles.append(t)
    print('reloaded wall from file')
    wall.draw(image)
    
def save_clicked():
    global tile_form, selected_tile, image, wall
    print("Values saved")
    selected_tile.w = int(tile_form.entries[0].get())
    selected_tile.h = int(tile_form.entries[1].get())
    selected_tile.wx = int(tile_form.entries[2].get())
    selected_tile.wy = int(tile_form.entries[3].get())
    selected_tile.l = int(tile_form.entries[4].get())
    selected_tile.t = int(tile_form.entries[5].get())
    selected_tile.r = int(tile_form.entries[6].get())
    selected_tile.b = int(tile_form.entries[7].get())
    image = clone.copy()
    wall.draw(image)
    tile_form.destroy()

def cancel_clicked():
    global tile_form
    print("Values not saved")
    tile_form.destroy()

def delete_clicked():
    global tile_form, wall, selected_tile, image
    print("Tile removed")
    wall.remove_tile(selected_tile)
    tiles.remove(selected_tile)
    image = clone.copy()
    wall.draw(image)
    tile_form.destroy()

def main(wall_file = None):
    global image, draw_tile, clone
    image = np.zeros((600, 600, 3), dtype = "uint8")
    clone = image.copy()

    cv2.namedWindow("image")
    cv2.setMouseCallback("image", mouse_callback)

    if wall_file:
        _load_wall(wall_file)

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
            
        elif key == ord("d"):
            draw_tile = not draw_tile

        elif key == ord("h"):
            help_popup()

        elif key == ord("s"):
            save_wall_popup()

        elif key == ord("l"):
            load_wall_popup()

        elif key == ord("w"):
            print(wall)
            print('gui tiles %d' % len(tiles))

            # if the 'c' key is pressed, break from the loop
        elif key == ord("c") or key == ord("q"):
            break

        # if there are two reference points, then crop the region of interest
        # from teh image and display it
    if len(refPt) == 2:
        roi = clone[refPt[0][1]:refPt[1][1], refPt[0][0]:refPt[1][0]]
        cv2.imshow("ROI", roi)
        cv2.waitKey(0)

    # close all open windows
    cv2.destroyAllWindows()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        wall_file = sys.argv[1]
    else:
        wall_file = None
    main(wall_file)
