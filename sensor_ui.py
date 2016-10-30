# Simulator Sensor UI
# 
# Author: Asuman Suenbuel
# (c) 2015
#

from sensor import *
from device_ui import *

from Tkinter import *
import tkMessageBox as messageBox
from tkFileDialog import askopenfilename
#from device import *
from sim_utils import *
import json,time
import threading

# --------------------------------------------------------------------------------
def createSensor(*args,**kwargs):
    if 'filename' in kwargs:
        return Sensor.createFromFile(kwargs['filename'])
    return SensorUI(*args,**kwargs)
# --------------------------------------------------------------------------------

class SensorUI(Sensor):

    
    def initStringVars(self):
        addStringVar(self,'name','Name')
        addStringVar(self,'unitName','Unit')
        addStringVar(self,'minValue','From',valueType='float')
        addStringVar(self,'maxValue','To',valueType='float')
        addStringVar(self,'startValue','Start Value',valueType='float')
        addStringVar(self,'varianceSeconds','During this many seconds',valueType='float')
        addStringVar(self,'varianceValue','the maximal difference of sensor values is',valueType='float')
        self.valueType = "Float" if self.isFloat else "Integer"
        addStringVar(self,'valueType','Value Type',values = ['Float','Integer'])
        addStringVar(self,'ndigitsAfterDecimalPoint','#Digits after decimal point',valueType='int')

    def buildUI(self,master):
        self.initStringVars()
        outerframe = Frame(master=master)
        f = Frame(outerframe)

        inputFields = Frame(f)
        rowcnt = 0
        createStringInput(self,'name',inputFields,rowcnt)
        rowcnt += 1
        createStringInput(self,'unitName',inputFields,rowcnt)
        rowcnt += 1
        inputFields.pack(anchor=W,expand=True)

        if self.isRealSensor:
            labelFrame = Frame(f)
            rowcnt0 = 0
            Label(labelFrame,text="This is a real sensor.").grid(row=rowcnt0,columnspan=3)
            rowcnt0 += 1
            if hasattr(self,'getRealInfo'):
                realInfoText = ""
                try:
                    realInfoText = self.getRealInfo.__call__(self)
                except:
                    try:
                        realInfoText = self.getRealInfo()
                    except:
                        pass
                Label(labelFrame,text = realInfoText).grid(row=rowcnt0,columnspan=3)
                rowcnt0 += 1
            Label(labelFrame,text="Current Value:").grid(row=rowcnt0,column=0)
            self.realValueLabel = Label(labelFrame,text="",width=8,bd=2,relief="sunken")
            self.realValueLabel.grid(row=rowcnt0,column=1)
            #Button(labelFrame,text="Update",command=self._updateRealValue).grid(row=1,column=2)
            labelFrame.pack()
            self._updateRealValueLoop()
            
        else:
            typeFrame = Frame(f)
            createStringInput(self,'valueType',typeFrame,0)
            typeFrame.pack(anchor=W)
            self.digitsFrame = Frame(f)
            createStringInput(self,'ndigitsAfterDecimalPoint',self.digitsFrame,row=0,width=6)
            self.digitsFrame.pack(anchor=W)

            valueRangeFrame = Frame(f,bd=1,relief=SUNKEN)
            Label(valueRangeFrame,text="Value Range",font="-weight bold").grid(row=0,columnspan=4,sticky=W)
            createStringInput(self,'minValue',valueRangeFrame,row=1,column=0,width=10)
            createStringInput(self,'maxValue',valueRangeFrame,row=1,column=2,width=10)
            createStringInput(self,'startValue',valueRangeFrame,row=2,width=10)
            valueRangeFrame.pack(fill=X,padx=5,pady=5)

            varianceFrame = Frame(f,bd=1,relief=SUNKEN)
            Label(varianceFrame,text="Variance (how quickly the sensor values change)",font="-weight bold").grid(row=0,columnspan=4,sticky=W)
            createStringInput(self,'varianceSeconds',varianceFrame,row=1,column=0,width=10)
            createStringInput(self,'varianceValue',varianceFrame,row=2,column=0,width=10)
            varianceFrame.pack(fill=X,padx=5,pady=5)

        buttonsFrame = Frame(f)
        if not (self.isRealSensor):
            Button(buttonsFrame,text = "Apply", command = lambda : self.applyUI(master)).grid(row=0,column=0,sticky=W)
        if (self.device != None) and (not (self.isRealSensor)):
            Button(buttonsFrame,text = "Remove from device", command = lambda : self.removeUI(master)).grid(row=0,column=1,sticky=W)

        cancelText = "Close" if self.isRealSensor else "Cancel"
        Button(buttonsFrame,text = cancelText, command = lambda : self.closeUI(master)).grid(row=0,column=2,sticky=E)
        buttonsFrame.pack(fill=X,padx=5,pady=5,expand=1)

        f.pack(fill=BOTH,padx=10,pady=10,expand=1);
        outerframe.pack(fill=BOTH,expand=1)
        master.title("Sensor \"" + self.name + "\"")

    def _updateRealValue(self):
        if hasattr(self,'realValueLabel'):
            label = self.realValueLabel
            value = None
            try:
                value = self.getRealValue.__call__(self)
            except:
                try:
                    value = self.getRealValue()
                except:
                    value = "*** error reading sensor value ***"
            label.config(text=str(value))

    def _updateRealValueLoop(self):
        self._updateRealValue()
        self.__updateRealValueTimer__ = threading.Timer(2,SensorUI._updateRealValueLoop,[self])
        self.__updateRealValueTimer__.start()
            
    def openAsToplevel(self):
        top = Toplevel()
        top.appObject = self
        self.buildUI(master = top)
        top.protocol("WM_DELETE_WINDOW", lambda : self.closeUI(top))
        #self.__root__.wait_window(top)
                   
    def buildFrameInDeviceUI(self,sensorsFrame,rowcnt,dialog=None):
        b = Button(sensorsFrame,text=self.name,bg="lightblue",width=25)
        b.grid(row=rowcnt,column=0,sticky=W)
        b['command'] = self.openAsToplevel
        self.dialog = dialog

    def applyUI(self,top):
        for field in self.stringVars.keys():
            updateValueFromStringVar(self,field)
        #special case:
        self.isFloat = self.valueType == 'Float'

        saveToFileUI(self)
        if self.device != None:
            self.device.updateSensorsFrame()
        self.closeUI(top)

    def removeUI(self,top):
        title = "Remove sensor?"
        msg = "Do you really want to remove this sensor from the device?"
        if messageBox.askyesno(title,msg):
            self.device.removeSensor(self)
            #self.device.updateSensorsFrame()
            if hasattr(self,'dialog') and self.dialog != None:
                self.dialog.updateSensorsFrame()
            self.closeUI(top)
    
    def closeUI(self,top):
        try:
            self.__updateRealValueTimer__.cancel()
        except:
            pass
        top.destroy()


