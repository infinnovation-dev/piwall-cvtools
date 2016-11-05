#!/usr/bin/env python

"""tkGui provides base classes for common tkinter front end development"""

cvsID = "$Id: fgcGui.py,v 1.9 2012/11/19 15:39:50 astephen Exp $"

import os
import re
import sys
import time
import traceback

# Python 2 (WAS)
#from Tkinter import *
# Python 3
from tkinter import *

# Python MegaWidgets module used in FGC Application.
# DEPENDENCY : pmw.sourceforge.net
# pip install pmw
import Pmw

from tkGuiUtils import Command, timestampAsString, Trace

from tkSkins import tk_skin

defaultDebug = 0

class Core:

    def __init__(self, gui):
        self.gui = gui
        self.debug = defaultDebug

class CoreTk(Core):
    """Handle the basic Tk setup and main window frame settings."""
    
    def __init__(self, gui, width=1267, height=995, appname = 'TK '):
        Core.__init__(self, gui)
        self.root = Tk()
        # Disable the close (Top right X and alt-f4)
        self.root.protocol('WM_DELETE_WINDOW', lambda: None)
        #tkSnack.initializeSnack(self.root)
        self.balloon = Pmw.Balloon(self.root)
        self.appname = appname
        self.root.title(self.appname)
        self.root.option_readfile('options.fonts')
        self.set_geometry(width, height)
        Pmw.initialise()
        self.prompt = StringVar()
        self.prompt.set("Python Console % ")
        self.buffer = StringVar()
        
        # Some useful examplew buffer commands
        # For AlarmsViewer
        self.buffer.set("print self.core.state.states['alarms_report'].viewers[0].alarmTable.root.grid_size()")
        self.console = None

        self.buildwidgets()

    def buildwidgets(self):
        self.mbar = Pmw.MenuBar()
        self.mbar.pack(fill=X)
        self.mbar.addmenu
# TODO: Add a Help menu when there is help to be displayed.
#        self.mbar.addmenu('Help', 'About %s' % self.appname, side='right')
        self.mbar.addmenu('File', 'File commands and Quit')

        self.mbar.addmenuitem('File', 'command', 'Quit this application',
                              label='Quit',
                              command=self.root.destroy)

        self.root.bind('<Control-Q>', self.quit)
        self.root.bind('<Control-q>', self.quit)
        self.root.bind('<q>', self.quit)


        self.mbar.addmenuitem('File', 'command', 'Console On',
                              label='Console On',
                              command=self.create_console)

        self.mbar.addmenuitem('File', 'command', 'Console Off',
                              label='Console Off',
                              command=self.destroy_console)

        self.interior = Frame(self.root)
        self.interior.pack(side=TOP, fill=X)

    def set_geometry(self, width=1267, height=995):
        self.width = width
        self.height = height
        self.root.geometry('%sx%s+0+0' % (self.width, self.height))

    def create_console(self, *args):
        self.consoleFrame = Frame(self.interior, bg='yellow', relief=RIDGE, bd=2)
        self.consoleFrame.pack(side=TOP, fill=X)
        self.consolePrompt = Label(self.consoleFrame, textvariable=self.prompt)
        self.consoleEntry = Entry(self.consoleFrame, textvariable = self.buffer, width=150, font="Verdana 10")
        self.consolePrompt.pack(side=LEFT, fill=X)
        self.consoleEntry.pack(side=LEFT, fill=X)
        self.consoleEntry.bind("<Return>", Command(self.console_cb))
        self.console = 1

    def destroy_console(self, *args):
        if self.console:
            self.consoleFrame.destroy()
            self.console = None

    def console_cb(self, *args):
        print("Console command = %s" % self.buffer.get())
        exec (self.buffer.get())
        print("Execed code")

    def quit(self, *args):
        self.root.destroy()

    def mainloop(self):
        self.root.mainloop()

keyPat = re.compile('''([a-z]+).([0-9]+)$''')

class CoreData(Core, Trace):
    """Data access wrapper"""

    def __init__(self, gui = None):
        Core.__init__(self, gui)
        Trace.__init__(self, trace = 0)
        pass

    def get(self, key, timestamp = None):
        pass

    def set(self, key, value):
        pass

### TODO: redesign the following support and integrate better with skins module.

class Gui(Trace):
    """Main engine."""
    
    def __init__(self, trace = 0, commissioningMode = 0, appname = 'TK ', release = 'devel', update_timeout_ms = 100):
        Trace.__init__(self, trace = trace)
        self.commissioningMode = commissioningMode
        ### TODO Extend for PF
        self.system = "TF"
        self.tk = CoreTk(self, appname = "%s : release %s" % (appname, release))
        self.data = CoreData(self)        

        self.skin = tk_skin
        
        self.plant = {}
        self.tags = []
        
        self.controller = None
        self.update_timeout = update_timeout_ms
        self.timestamp = time.time()
        self.time_started = time.time()
        self.time_elapsed = 0
        self.restarted = 0
        self.startup_sound()

        self.widgets = {}

    def add_widget(self, key, w):
        # We maintain a mapping between signal keys and related widgets whose colour
        # must be conditioned on the signal state.   In the first instance, the logic
        # of the conditioning is presence/absence of alarm, and is implemented in the
        # update_backgrounds method of the AlarmsDictList class.
        self.widgets.setdefault(key, []).append(w)

    def startup_sound(self):
        pass
        #os.spawnl(os.P_NOWAIT, './tk_gui_play_startup_sound.py')
        #os.spawnl(os.P_NOWAIT, './tk_gui_initialize_siren.py')
        
    def add(self, plant_value, tag = None, core_data = None):
        if not tag:
            tag = plant_value.tag
        if tag not in self.tags:
            self.plant[tag] = plant_value
            self.tags.append(tag)
        plant_value.set_core_data(core_data)
        self.trace_2("Added plant_value %s\n", tag)

    def get(self, tag):
        return self.plant[tag]

    def reset_timestamp(self, timestamp=None):
        self.trace_2("Timestamp was %s\n", self.timestamp)
        self.trace_2("Set timestamp to %s\n", timestamp)
        if timestamp:
            self.timestamp = timestamp
        else:
            self.timestamp = time.time()
            self.time_started = self.timestamp
            self.restarted+=1
        
    def reset_timeout(self, timeout_ms):
        self.update_timeout = timeout_ms

    def update(self):
        self.timestamp = time.time()
        self.elapsed = self.timestamp - self.time_started
        for tag in self.tags:
            self.trace_3("Gui update : %s plant value tagged %s at %s\n", self.plant[tag].__class__,
                                                                           tag,
                                                                           time.time())
            self.plant[tag].update(self.elapsed)
            self.trace_3("GUI update called for %s\n", self.elapsed)
        self.tk.root.after(self.update_timeout, self.update)
        
    def mainloop(self):
        self.tk.root.after(self.update_timeout, self.update)
        self.tk.mainloop()

    def oneloop(self):
        self.update()


class ViewerGui:

    def __init__(self, gui, standalone = 0, commissioningMode = 0):
        self.gui = gui
        self.controller = self.gui.controller
        self.standalone = standalone
        
        if commissioningMode == 1:
            self.commissioningMode = 1
        else:
            self.commissioningMode = gui.commissioningMode

if __name__ == '__main__':
    gui = Gui()
    state = gui.data.get('state')
    print(state)
    gui.startup_sound()
    gui.mainloop()
    

    
    
