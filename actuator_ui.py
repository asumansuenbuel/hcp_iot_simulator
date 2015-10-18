# Actuator UIs
# 
# Author: Asuman Suenbuel
# (c) 2015
#

from Tkinter import *
from actuator import *
import resources


class LedUI(Led):

    def __init__(self,*args,**kwargs):
        Led.__init__(self,*args,**kwargs)
        self.onImage = self.id + "-on"
        self.offImage = self.id + "-off"
        resources.images[self.onImage] = "images/" + self.onImage + "_24.gif"
        resources.images[self.offImage] = "images/" + self.offImage + "_24.gif"


    def initUI(self,frame):
        imageName = self.onImage if self.isOn else self.offImage
        valueText = "on" if self.isOn else "off"
        self.label = Label(frame,image=resources.getImage(imageName))
        self.label.pack(side='left')
        self.valueLabel = Label(frame,text=valueText)
        self.valueLabel.pack(side='left')

    def refreshUI(self):
        imageName = self.onImage if self.isOn else self.offImage
        valueText = "on" if self.isOn else "off"
        self.label.configure(image=resources.getImage(imageName))
        self.valueLabel.configure(text=valueText)
        
    def processMessage(self,message):
        wasOn = self.isOn
        Led.processMessage(self,message)
        if self.isOn != wasOn:
            self.refreshUI()

