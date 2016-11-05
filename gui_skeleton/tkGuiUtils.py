#!/usr/bin/env python

import time, string, sys, syslog

from tkinter import *

import Pmw

#import tkSnack

class Trace:

    """Trace class, designed to be inherited from.   If python -O, then __debug__ is false, and the
    print and test code all becomes ignored completely i.e. minimal run-time overhead if any."""

    stdout = sys.stdout
    stderr = sys.stderr
    
    def __init__(self, trace = 0, prefix = ''):
        self.trace = trace
        if prefix == '':
            absoluteClass = "%s" % self.__class__
            className = ''.replace(absoluteClass, "%s." % self.__module__)
            self.prefix = "%s (0x%08X)" % (className, id(self))

    def redirectToFile(self, stdoutPath, stderrPath):
        stdoutFh = open(stdoutPath, "a")
        stderrFh = open(stderrPath, "a")
        self.stdout = stdoutFh
        self.stderr = stderrFh

    def resetOutputPaths(self):
        self.stdout.close()
        self.stderr.close()
        self.stdout = sys.stdout
        self.stderr = sys.stderr

    def tracePrint(self, format, *args):
        if __debug__:
            indentation = "\t" * (self.trace - 1)
            self.stdout.write("TR%1d %s%s : %s" % (self.trace, indentation, self.prefix, format % args))
            
    def trace_1(self, *args):
        """Generally use for once per application calls, e.g. __init__"""
        if __debug__:
            if self.trace >= 1:
                self.tracePrint(*args)

    def trace_2(self, *args):
        """General use for multiple, but infrequent calls."""
        if __debug__:
            if self.trace >= 2:
                self.tracePrint(*args)

    def trace_3(self, *args):
        """Generally use for repetitive, normal calls."""
        if __debug__:
            if self.trace >= 3:
                self.tracePrint(*args)

    def trace_4(self, *args):
        """Generally use where providing debug information, or in __repr__ methods for detail."""
        if __debug__:
            if self.trace >= 4:
                self.tracePrint(*args)

    def trace_5(self, *args):
        """Let's hope we don't need this one."""
        if __debug__:
            if self.trace >= 5:
                self.tracePrint(*args)

    def trace_w(self, *args):
        """Warnings of code conditions which ought not to happen.   Can be conditioned out in extremis."""
        if __debug__:
            self.tracePrint(*args)
            


# Local module trace variable for functions within the module
trace = Trace(trace = 0)

def center_pad(s, size):    
    if (size % 2): size -= 1
    

def tk_exit(root):
    print("Exiting")
    root.destroy()

def frame(root, side, expand=YES, fill=BOTH):
    w = Frame(root)
    w.pack(side=side, expand=expand, fill=fill)
#    w.pack(side=side)
    return w

def label(root, side, text):
    w = Label(root, text=text, borderwidth=2, relief=GROOVE)
    w.pack(side=side, expand=YES, fill=BOTH)
    return w

def textLabel(root, text, side, sticky=W, width=10, anchor=N):
    w = Label(root, text=text, borderwidth=2, relief=GROOVE, width=width, anchor = anchor)
    w.pack(side=side, expand=YES, fill=BOTH)
    trace.trace_1("Added Text Label %s\n", text)
    return w

def textVariableLabel(root, textvariable, side, width=10, sticky=W, anchor=N):
    w = Label(root, textvariable=textvariable, borderwidth=2, relief=GROOVE, width=width, anchor=anchor)
    w.pack(side=side, expand=YES, fill=BOTH)
    trace.trace_1("Added Text Variable %s\n", textvariable)
    return w

def ____gridTextLabel(root, row, col, text, sticky=W, width=10, anchor=N):
    w = Label(root, text=text, borderwidth=2, relief=GROOVE, width=width, anchor=anchor)
    w.grid(row=row, column=col, sticky=sticky)
    trace.trace_1("Added Text Label %s at (%d,%d)\n", text, row, col)
    return w

def ____gridTextVariableLabel(root, row, col, textvariable, width=10, sticky=W, anchor=N):
    w = Label(root, textvariable=textvariable, borderwidth=2, relief=GROOVE, width=width, anchor=anchor)
    w.grid(row=row, column=col, sticky=sticky)
    trace.trace_1("Added Text Variable %s at (%d,%d)\n", textvariable, row, col)
    return w

### TODO: refactor : trap any other references to strftime

def timestampAsString(timestampFromVxWorks):
    """VxWorks will be given a local time seconds since Epoch to cope with DST.  Translate back before
    remapping the time to local time."""
    try:
        timestamp = utc_seconds(int(timestampFromVxWorks))
        datestring = time.strftime("%a %b %d %Y %H:%M:%S", time.localtime(timestamp))
    except:
        datestring = "Invalid timestamp %s" % timestamp
    return datestring

def timestampAsShortString(timestampFromVxWorks):
    """VxWorks will be given a local time seconds since Epoch to cope with DST.  Translate back before
    remapping the time to local time. Use two digit year field for user interface because of constraints."""
    try:
        timestamp = utc_seconds(int(timestampFromVxWorks))
        datestring = time.strftime("%a %d %b %y %H:%M:%S", time.localtime(timestamp))
    except:
        datestring = "Invalid timestamp %s" % timestamp
    return datestring

def timestampAsStepHistoryString(timestampFromVxWorks):
    try:
        timestamp = utc_seconds(int(timestampFromVxWorks))
        datestring = time.strftime("%d/%m/%y %H:%M:%S", time.localtime(timestamp))
    except:
        datestring = "Invalid timestamp %s" % timestamp
    return datestring

def timestampAsWarehousePath(timestampFromVxWorks):
    """VxWorks will be given a local time seconds since Epoch to cope with DST.  Translate back before
    remapping the time to local time."""
    try:
        timestamp = utc_seconds(int(timestampFromVxWorks))
        datestring = time.strftime("%Y-%b-%d@%H:%M:%S", time.localtime(timestamp))
    except:
        datestring = "Invalid timestamp %s" % timestamp
    return datestring

#
# REFACTOR: Move to fgcSkins.py
#

lampColourBeige = '#FFFFE6'
lampColourRed = '#FF0000'
lampColourMagenta = '#FF00FF'


class AudioController:

    def __init__(self, gain = 4):
        self.gain = 1
    
    def on(self):
        # tkSnack.audio.play_gain(self.gain)
        pass

    def off(self):
        # tkSnack.audio.play_gain(0)
        pass

class AnnunciatorLamp(Trace):
    
    def __init__(self, frame, text, command = None):
        Trace.__init__(self, trace = 0)
        self.frame = frame
        self.text = text
        self.normal_bg = lampColourBeige
        self.abnormal_bg = lampColourRed
        self.button = None
        self.state_cb = None
        self.flash_cb = None
        self.command = command
        self.build_button(self.text, self.command)
                   
    def build_button(self, text, command):
        l = Button(self.frame, text = text, bg = self.normal_bg, fg = 'black')
        l.pack(side=LEFT, expand=YES, fill=X) 
        l.configure(font = "Helvetica 12 bold")
        if command:
            l.configure(command = command)
        self.button = l

    def set_normal_bg(self, colour):
        self.normal_bg = colour

    def set_abnormal_bg(self, colour):
        self.abnormal_bg = colour
    
    def update(self):
        value = self.state_cb()
        self.trace_3("Updated %s by calling %s value is %s", self, self.state_cb, value)
        if value > 0:
            self.button.configure(bg = self.abnormal_bg)
        else:
            self.button.configure(bg = self.normal_bg)            

    def __repr__(self):
        return "Lamp: %s" % self.text

class StateTriggeredAnnunciatorLamp(AnnunciatorLamp):
    
    def __init__(self, frame, text, onvar, flashvar):
        AnnunciatorLamp.__init__(self, frame, text)
        self.state = 0 
        self.state_cb = Command(onvar.get)
        self.flash_cb = Command(flashvar.get)

    def update(self):
        flash = self.flash_cb()
        if flash:
            self.state = (1 - self.state)
        else:
            self.state = self.state_cb()

        if self.state > 0:
            self.button.configure(bg = self.abnormal_bg)
        else:
            self.button.configure(bg = self.normal_bg)            
        

class DigitalTriggeredAnnunciatorLamp(AnnunciatorLamp):
    
    def __init__(self, frame, text, signal_name, tk_digital, cat):
        AnnunciatorLamp.__init__(self, frame, text)
        self.text = text
        self.signal_name = signal_name
        self.tk_digital = tk_digital
        self.link_trigger(cat)

    def link_trigger(self, cat):
        found = 1
        try:
            sig = cat.dict['digitalInputsByName'][self.signal_name]
        except KeyError:
            found = 0

        if not found:
            found = 1
            try:
                sig = cat.dict['digitalOutputsByName'][self.signal_name]
            except KeyError:
                found = 0

        if not found:
            print("Failed to link lamp for %s : not located in catalogue" % key)
        else:
            self.state_cb = Command(self.tk_digital.get_value, sig.channel)


class Command(Trace):
    def __init__(self, func, *args, **kw):
        Trace.__init__(self, trace = 0)
        self.func = func
        self.args = args
        self.kw = kw
    def __call__(self, *args, **kw):
        args = self.args + args
        kw.update(self.kw)
        return self.func(*args, **kw)
    def __repr__(self):
        func_rep = string.split("%s" % self.func)[0]
        rep = "Command object with func %s" % func_rep
#        for a in self.args:
#            rep += "Arg %s" % 
        return rep

class CommandWithOkCancelDialog(Trace):

    def __init__(self, root, title, text, func, *args, **kw):
        Trace.__init__(self, trace = 0)
        self.root = root
        self.title = title
        self.text = text
        self.func = func
        self.args = args
        self.kw = kw
        self.trace_1("OK Cancel dialog created\n")
        syslog.openlog("tkController", syslog.LOG_LOCAL0)


    def __call__(self, *args, **kw):

        self.trace_3("OK Cancel Dialog called %s", "Hello World")
        
        dialog = Pmw.Dialog(self.root,
                            buttons = ('OK', 'Cancel'),
                            defaultbutton = 'Cancel',
                            title = self.title)
        
        w = Label(dialog.interior(),
                  text=self.text,
                  background='black',
                  foreground='white',
                  pady=20)
        
        w.pack(expand=1,
               fill=BOTH,
               padx=4,
               pady=4)
        
        result = dialog.activate()
    
        print("Result was %s" % result)
        if result == 'OK':
            syslog.syslog(syslog.LOG_INFO, "#fgcctrl %s invoked OK" % self.text)
            args = self.args + args
            kw.update(self.kw)
            return self.func(*args, **kw)
        else:
            syslog.syslog(syslog.LOG_INFO, "#fgcctrl %s CANCEL" % self.text)
            


class Options:

    def __init__(self, name, *args, **kw):
        self.name = name
        self.opts = {}
        for k in list(kw.keys()):
            self.opts[k] = kw[k]

    def add(self, key, value):
        self.opts[key] = value

    def wapply(self, widget):
        woptions = list(widget.keys())
        for k in list(self.opts.keys()):
            if k in woptions:
                widget.configure(k = self.opts[k])

    
    def __repr__(self):
        rep = "Options %s\n" % self.name
        for k in list(self.opts.keys()):
            rep += "%s = %s\n" % (k, self.opts[k])
        return rep


optNoteBookStandard = Options("Standard notebook",
                              font = "Verdana 8",
                              background = "lightyellow",
                              foreground = "blue")


    
def is_dst():
    return bool(time.localtime().tm_isdst)

def local_seconds():
    """Determine local time, and express in seconds since the Epoch.   Used to set the VxWorks clock,
    which could use UTC hw clock and map to local times through TIMEZONE variable, but we would then have
    to keep the TIMEZONE variable up to date."""
    utc_seconds = time.time()
    if is_dst():
        return utc_seconds + 3600
    else:
        return utc_seconds

def utc_seconds(seconds):
    if is_dst():
        return seconds - 3600
    else:
        return seconds


if __name__ == '__main__':
    from tkinter import *

    Tk()
    d = Digital()
    for sr in [0,1]:
        for card in range(0,16):
            d.set_channels(sr,card,((sr << 12) | card))
    print(d)

    cat = SigCatalogue()
    makeCatalogue(cat)

    dtk = DigitalTk(cat)
    dtk.update(d)
    print(dtk)

    channel = 1
    cmd = Command(dtk.get_value,  channel)
#    print cmd
    value = cmd.__call__()
    value = apply(cmd)
    v = cmd()
    print(v)
    print("Channel 1 has value %s" % v)
