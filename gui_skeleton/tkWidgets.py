#!/usr/bin/env python

"""Support for managing widgets in the fgc application."""

from tkinter import *

from tkGuiUtils import Trace

from tkSkins import tk_skin

### WIBNI : In development, track use of widgets in classes automatically for refactoring reports.

class TkW(Trace):
    """Generic TkWidget behaviour which can be mixed with Tk custom widgets."""

    instances = []

    def __init__(self):
        Trace.__init__(self, trace = 0)
        self.instances.append(self)

    def usage_report(self):
        print("%d instances of class %s" % (len(self.instances), self.__class__))

### --------------------------------------------------------------------------------------------------------------------
### Generic widgets : reused in a number of classes.
### --------------------------------------------------------------------------------------------------------------------
        
class gridTextLabel(TkW, Label):

    def __init__(self, root, row, col, text, sticky=W, width=10, anchor='center'):
        TkW.__init__(self)
        Label.__init__(self, root, text=text, borderwidth=2, relief=GROOVE, width=width, anchor=anchor)
        self.grid(row=row, column=col, sticky=sticky)
        self.trace_3("Added Text Label %s at (%d,%d)\n", text, row, col)

        
class gridTextVariableLabel(TkW, Label):

    def __init__(self, root, row, col, textvariable, width=10, sticky=W, anchor='center', columnspan=1):
        TkW.__init__(self)
        #Label.__init__(self, root, textvariable=textvariable, borderwidth=2, relief=GROOVE, width=width, anchor=anchor)
        Label.__init__(self, root, textvariable=textvariable, borderwidth=2, relief=GROOVE, width=width, anchor = anchor)
        self.grid(row=row, column=col, sticky=sticky, columnspan = columnspan)
        self.trace_1("widget bound to text variable %s at (%d,%d)\n", textvariable, row, col)

    def condition_by_alarm(self, displayed, on, acked):
        if not displayed:
            self.configure(bg = fgc_skin.rgb('default_variable_label_bg'))
            return
        if on :
            if acked:
                self.configure(bg = fgc_skin.rgb('alarm_on_acked_variable_label_bg'))
            else:
                self.configure(bg = fgc_skin.rgb('alarm_on_not_acked_variable_label_bg'))
        else:
            # Displayed and not on means it cannot have been acknowledged, so there is only one valid case.
            # Anything else is a bug : and really is impossible.
            if not acked:
                self.configure(bg = fgc_skin.rgb('alarm_off_not_acked_variable_label_bg'))
            else:
                self.trace_w('Inconsistent alarm state : not displayed, not on, but acknowledged.')
                self.configure(bg = fgc_skin.rgb('alarm_BUG_variable_label_bg'))


def gridButton(root, row, col, text, command, columnspan = 1, width=10, bg='lightgreen'):
    w = Button(root, text=text, borderwidth=2, relief=GROOVE, command=command, bg = bg)
    w.grid(row=row, column=col, columnspan = columnspan, sticky=N+W+S+E)
    return w


### --------------------------------------------------------------------------------------------------------------------
### Specific widgets : reused in one or few classes : consider refactoring.
### --------------------------------------------------------------------------------------------------------------------


def shortlistLabel(root, row, col, textvariable, sticky=N+W+S+E, anchor=W):
    w = Label(root, textvariable=textvariable, borderwidth=2, relief=GROOVE, width=40, bg='white', anchor=anchor, justify='left')
    w.grid(row=row, column=col, sticky=sticky)
    #print "Added Text Variable %s at (%d,%d)" % (textvariable, row, col)
    return w

        


if __name__ == '__main__':
    r = Tk()
    text = StringVar()
    text.set('Hello World')
    l = gridTextVariableLabel(r, 0, 0, text)    
    l = gridTextVariableLabel(r, 0, 0, text)
    
    r.mainloop()
