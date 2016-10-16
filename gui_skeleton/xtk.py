#!/usr/bin/env python

'''
xtk : Generic tkinter GUI front end for the kind of objects I often need to control.
'''

# General model is that sets of linked objects will update the views.

from collections import OrderedDict

# TODO: pep8 one per line.
from functools import partial
import errno
import pickle
import re
import time
import os 
import struct
import sys 
import string

import pdb

from tkinter import *
from tkinter.ttk import *

from bitstring import Bits

import Pmw

from tkGui import *

from tkGuiUtils import *

from tkWidgets import *

class PlantValue:
    def __init__(self, observer):
        pass
    pass

class ViewerGui:
    pass

class TrafficLightObject(PlantValue):
    tag = 'trafficlight'
    def __init__(self, trace = 0):
        self.red = False
        self.amber = False
        self.green = False
        self.lastupdate = 0

    def get_val(self):
        val = 0
        if self.green:
            val += 1
        if self.amber:
            val += 2
        if self.red:
            val += 4
        return val

    def set_val(self, val):
        if (val & 0x1) == (0x1) :
            self.green = True
        else:
            self.green = False
        if (val & 0x2) == (0x2) :
            self.amber = True
        else:
            self.amber = False
        if (val & 0x8) == (0x8) :
            self.red = True
        else:
            self.red = False
        return None
    
    def update(self, timestamp = None):
        data = self.core_db.get(self.tag, timestamp)
        # TODO: map data into self.relays state
        # Run the PlantValue update method to trigger all connectors and viewer changes.
        PlantValue.update(self)

class TrafficLightObserver(Trace):
    '''StringVar representation of a relay'''
    def __init__(self, object):
        Trace.__init__(self, trace = 0)
        # Link to the real world
        self.object = object
        # Internal state to update GUI/CLI
        self.tkstate = StringVar()
        self.tktooltip = StringVar()
        self.tkdetail = StringVar()
        self.tkval = StringVar()
        self.tkdesc = StringVar()
        self.val = -1

    def set(self, val):
        was = self.val
        self.val = val
        self.object.set_val(self.val)
        if (was != self.val): # Only update on change.
            text = "Invalid value (not 1,2, or 3)"  # Ensure translation works
            if self.val == 0:
                text = self.off_text
            if self.val == 1:
                text = self.on_text.upper()
            self.tkstate.set(text)
            self.tktooltip.set("Relay box channel %d %s : %d => %s" % (self.channel, self.description, self.val, text))
            self.tkdetail.set("%s reads %d : %s" % (self.description, self.val, text))
            self.tkdesc.set("%s" % self.description)
            self.tkval.set("%s (%s)" % (text, self.val))

    def __repr__(self):
        return self.tktooltip.get()

class TrafficLightGui(Frame, ViewerGui):
    def __init__(self, observer, gui, root):
        #ViewerGui.__init(self, gui)
        self.cname = self.__class__.__name__
        self.observer = observer
        self.gui = gui
        self.root = root
        self.balloon = self.gui.tk.balloon
        Frame.__init__(self, root)
        self.pack(expand=YES, fill=BOTH)
#        self.configure(bg='red')
        self.build_widgets()

    def build_widgets(self, cols = 2):
        """Using the grid packer."""
        f = frame(self, TOP)
        # Relay Information Frame (rf)
        rf = frame(f, TOP, expand=NO, fill=X)
        self.build_relay_frame(rf)
        # Sumamry Information Frame (sf)
        sf = frame(f, TOP, expand=NO, fill=X)
        self.build_summary_frame(sf, self.with_capacitor_info)
        
    def build_relay_frame(self, root, cols = 2):
        col = 0
        row = 0
        srf = frame(root, TOP)

        for r in self.relayBoxTk.relays:
            rl = self.relayBoxTk.relayViewer[r]
            label_name = 'relay %d' % r
            label = gridTextLabel(srf, row, col, "%s" % label_name, sticky = N+W+E+S, width=5)
            # FIXME : Need theme support 
            label.configure(bg='#C7C7D4')
            col += 1
            
            var = rl.tkstate
            label = gridTextVariableLabel(srf, row, col, var, sticky = N+W+E+S)
            # FIXME : Need theme support
            label.configure(bg='#CCFFFF')
            col += 1
            # Register the widget for updates on alarm changse.
            self.gui.add_widget('%s' % label_name, label)

            var = rl.tkdesc
            label = gridTextVariableLabel(srf, row, col, var, sticky = N+W+E+S)
            # FIXME : Need theme support
            label.configure(bg='#CCFFFF')
            col += 1
            # Register the widget for updates on alarm changse.
            self.gui.add_widget('%s' % label_name, label)

            cols = col

            if col == cols:
                col = 0
                row += 1

        for i in range(0, cols):
            if (i % 2):
                srf.grid_columnconfigure(i, weight=2)
            else:
                srf.grid_columnconfigure(i, weight=1)

        for i in range(0, row):
            srf.grid_rowconfigure(i, weight=1)

    def build_summary_frame(self, root, with_capacitor_info = False):
        srf = frame(root, TOP)        
        labels = []

        if with_capacitor_info:

            label = gridTextLabel(srf, 0, 0, "Total Capacitance", sticky = N+W+E+S, width=5)
            labels.append(label)
            
            var = self.relayBoxTk.totalCapacitance
            label = gridTextVariableLabel(srf, 0, 1, var, sticky = N+W+E+S)
            labels.append(label)

        label = gridTextLabel(srf, 1, 0, "Relay Pattern", sticky = N+W+E+S, width=5)
        labels.append(label)

        var = self.relayBoxTk.relayPattern
        label = gridTextVariableLabel(srf, 1  , 1, var, sticky = N+W+E+S)
        labels.append(label)

        for l in labels:
            l.configure(bg='#C7C7D4')

        for i in range(0, 2):
            if (i % 2):
                srf.grid_columnconfigure(i, weight=2)
            else:
                srf.grid_columnconfigure(i, weight=1)

        for i in range(0, 2):
            srf.grid_rowconfigure(i, weight=1)

def main(devRunMode, capacitor_pane = True, motor_pane = True):
    # GUI.            
    show_warning = False
    commissioningMode = 0
    
    options = {
        'capacitor' : True,
        'motor' : True
    }

    gui = Gui(appname='Skeleton TK UI', release = 'Alpha 1.0',update_timeout_ms = 100)

    mainFrame = Frame(gui.tk.root, relief = GROOVE, bg='lightgreen', borderwidth = 5, height=800)
    mainFrame.pack(side=TOP, expand=YES, fill=BOTH)

    ctrlFrame = Frame(mainFrame, relief=GROOVE, bg='black', width=300, borderwidth=2)
    ctrlFrame.pack(side=LEFT, expand=YES, fill=BOTH)
    ctrlFrame.grid(row=0, column=0, sticky=N+S+E+W)

    gui.ctrlFrame = ctrlFrame

    devRunOptions = ['real', 'mock']

    if devRunMode == 'real':
        pass
    elif devRunMode == 'mock':
        pass
    else:
        print('devRunMode not in options.  %s.  Bail' % devRunOptions)
        sys.exit(2)

    nbFrame = Frame(mainFrame, relief=RAISED, bg='#CFCDCD', borderwidth=1)
    nbFrame.pack(side=LEFT, expand=YES, fill=BOTH)
    nbFrame.grid(row=0, column=1, sticky=N+S+E+W)

    mainFrame.grid_rowconfigure(0, weight=1)
    mainFrame.grid_columnconfigure(0, weight=0, minsize=350)
    mainFrame.grid_columnconfigure(1, weight=1)

    nb = ttk.Notebook(nbFrame)

    relayFrame = Frame(nb, relief=RAISED, bg='#CFCDCD', borderwidth=1)
    relayFrame.pack(side=LEFT, expand=YES, fill=BOTH)
    relayFrame.grid(row=0, column=1, sticky=N+S+E+W)

    gui.relayFrame = relayFrame

    p_relays = nb.add(relayFrame, text = 'Relays')
    nb.pack(padx=5, pady=5, fill=BOTH, expand=1)

    gui.mainloop()
    
if __name__ == '__main__':
    # TODO : wrap up the following in a proper set of reusable components at CLI.
    try:
        devRunMode = sys.argv[1]
        print(devRunMode)
    except:
        print("Check the usage.")
        sys.exit(1)

    if devRunMode == 'real':
        main(devRunMode)
    elif devRunMode == 'mock':
        main(devRunMode)
        
    sys.exit(3)
