#!/usr/bin/env python

"""Support for managing colour, font, icon support for tkinter applications."""

from tkinter import *

# TODO: Improve the palette.

palette_colours = {
    'blue' : '#0000FF',
    'light_gray_blue' : '#C7C7D4',
    'light_cyan' : '#C7D6CA',
    'red' : '#FF0000',
    'crimson' : '#DC143C',
    'light_red' : '#FF3E3B',
    'emergency_red' : '#FF0000',
    'light_orange' : '#FAC32D',
    'light_yellow' : '#FAFAD2',
    'bug_magenta' : '#BA55D3'
    }

default_skin = {
    'default_text_label_bg' : palette_colours['light_gray_blue'],
    'default_variable_label_bg' : palette_colours['light_cyan'],
    'default_variable_label_bg' : palette_colours['light_cyan'],
    'alarm_on_not_acked_variable_label_bg' : palette_colours['emergency_red'],
    'alarm_on_acked_variable_label_bg' : palette_colours['light_yellow'],
    'alarm_off_not_acked_variable_label_bg' : palette_colours['light_orange'],
    'alarm_BUG_variable_label_bg' : palette_colours['bug_magenta'],
    'variable_in_alarm_label_bg' : palette_colours['emergency_red'],
    'default_control_button_bg' : palette_colours['light_orange'],
    'default_safe_control_button_bg' : palette_colours['light_yellow'],
    'emergency_shutdown_label_bg' : palette_colours['emergency_red'],
    'sequence_selected_bg' : palette_colours['light_orange'],
    'step_control_bg' : palette_colours['light_orange'],
    'alarm_red' : palette_colours['light_red']
}

from tkGuiUtils import *

class Skin:
    def __init__(self, cdict):
        self.cdict = cdict
        self.default_colour = '#000000'
        self.widgets = {}
        self.rgb_used = {}
        self.colour_used = {}
        pass

    def rgb(self, colour):
        try:
            return self.cdict[colour]
        except:
            try:
                return palette_colours[colour]
            except:
                return self.default_colour

    def set_bg(self, widget, colour):
        rgb = self.rgb(colour)
        self.set_bg_by_rgb(widget, rgb)
        
    def set_bg_by_rgb(self, widget, rgb):
        wkey = "%s" % widget
        if wkey not in list(self.widgets.keys()):
            self.widgets[wkey] = {}
        self.widgets[wkey]['bg'] = rgb
        widget.configure( bg = rgb )
        if rgb not in list(self.rgb_used.keys()):
            self.rgb_used[rgb] = []
        self.rgb_used[rgb].append(widget)        

    def change_bg(self, old, new):
        rgb_old = self.rgb(old)
        rgb_new = self.rgb(new)
        self.change_bg_by_rgb(rgb_old, rgb_new)

    def change_bg_by_rgb(self, rgb_old, rgb_new):
        for w in self.rgb_used[rgb_old]:
            self.rgb_used[rgb_old].remove(w)
            self.set_bg_by_rgb(w, rgb_new)

    def __repr__(self):
        rep = ""
        rep += "Skin container for %d widgets" % len(list(self.widgets.keys()))
        for rgb in list(self.rgb_used.keys()):
            print("Colour %s : %d widgets" % (rgb, len(self.rgb_used[rgb])))
        return rep

    def show(self):
        print(self)

DefaultSkin = Skin(default_skin)

tk_skin = DefaultSkin

if __name__ == '__main__':
    root = Tk()
    DefaultSkin = Skin(default_skin)
    b = Button(root, text = "Quit", command = sys.exit)
    b.pack()
    b = Button(root, text = "Show", command = DefaultSkin.show)
    b.pack()
    b = Button(root, text = "Emergency Red", command = Command(DefaultSkin.change_bg, 'blue', 'emergency_red', ))
    b.pack()
    DefaultSkin.set_bg(b, 'emergency_red')

    b = Button(root, text = "Alternative", command = Command(DefaultSkin.change_bg, 'emergency_red', 'blue'))
    b.pack()

    for d in tk_skin.cdict:
        c = Button(text = d, bg = tk_skin.rgb(d))
        c.pack()
    root.mainloop()
    

