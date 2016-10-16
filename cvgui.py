#!/usr/bin/env python
# -*- coding: utf-8 -*-
  
"""
"""
 
import Tkinter as Tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

MINIMUM_RESIZE_WIDTH = 10

class WallModel():
 
    def __init__(self):
        self.refPt = []
        self.image = np.zeros((600, 600, 3), dtype = "uint8")
        self.clone = image.copy()
        self.wall = Wall(600, 600, None, "testWall")
        
        self.selected_tile = None
        self.updated_tile = None
        self.tile_form = None
        self.tiles = []
        self.draw_tile = True

        # tile dragging helpers
        self.l_mouse_button_down = False
        self.mouse_over_tile = False
        self.offsets = (0,0)
        
        self.generated_piwall = "generatedpiwall"
        
  
class View():
    def __init__(self, master):
        self.frame = Tk.Frame(master)
        self.fig = Figure( figsize=(7.5, 4), dpi=80 )
        self.ax0 = self.fig.add_axes( (0.05, .05, .90, .90), axisbg=(.75,.75,.75), frameon=False)
        self.frame.pack(side=Tk.LEFT, fill=Tk.BOTH, expand=1)
        self.sidepanel=SidePanel(master)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame)
        self.canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
        self.canvas.show()
 
class SidePanel():
    def __init__(self, root):
        self.frame2 = Tk.Frame( root )
        self.frame2.pack(side=Tk.LEFT, fill=Tk.BOTH, expand=1)
        self.plotBut = Tk.Button(self.frame2, text="Plot ")
        self.plotBut.pack(side="top",fill=Tk.BOTH)
        self.clearButton = Tk.Button(self.frame2, text="Clear")
        self.clearButton.pack(side="top",fill=Tk.BOTH)
  
class Controller():
    def __init__(self):
        self.root = Tk.Tk()
        self.model=Model()
        self.view=View(self.root)
        self.view.sidepanel.plotBut.bind("<Button>",self.my_plot)
        self.view.sidepanel.clearButton.bind("<Button>",self.clear)
  
    def run(self):
        self.root.title("Tkinter MVC example")
        self.root.deiconify()
        self.root.mainloop()
         
    def clear(self,event):
        self.view.ax0.clear()
        self.view.fig.canvas.draw()
  
    def my_plot(self,event):
        self.model.calculate()
        self.view.ax0.clear()
        self.view.ax0.contourf(self.model.res["x"],self.model.res["y"],self.model.res["z"])
        self.view.fig.canvas.draw()

if __name__ == '__main__':
    c = Controller()
    c.run()
