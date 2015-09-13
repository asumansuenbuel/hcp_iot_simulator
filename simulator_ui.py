#
# Simulator UI interface (class SimulatorUI)
#
# 
# Author: Asuman Suenbuel
# (c) 2015
#


from Tkinter import *
import tkMessageBox as messageBox

from simulator import *

from device_ui import *
from sim_utils import *

import sys
# ================================================================================

# --------------------------------------------------------------------------------
def createSimulator(*args,**kwargs):
    if 'filename' in kwargs:
        return SimulatorUI.createFromFile(kwargs['filename'])
    return SimulatorUI(*args,**kwargs)
# --------------------------------------------------------------------------------

class SimulatorUI(Simulator):

    @staticmethod
    def createFromFile(filename):
        evalstr = getFileContents(filename)
        obj = eval(evalstr)
        if not isinstance(obj,SimulatorUI):
            raise Exception('object created from file "' + filename + '" is not a Simulator.')
        return obj
    
    def buildUI(self,master):
        addStringVar(self,'name','Name of Simulator')
        outerframe = Frame(master)
        f = Frame(outerframe)

        inputFields = Frame(f)
        rowcnt = 0
        createStringInput(self,'name',inputFields,rowcnt)
        inputFields.pack(anchor=W,expand=True)

        deviceSection = Frame(f,relief=SUNKEN,bd=1)
        rowcnt = 0
        Label(deviceSection,text="Devices",font="-weight bold").grid(row=rowcnt,sticky=W)
        rowcnt += 1

        self.devicesFrame = Frame(deviceSection)
        self.devicesFrame.grid(row=rowcnt,columnspan=5,pady=5,sticky=W)
        rowcnt += 1

        b = Button(deviceSection, text = "Add New Device", command = self.createDeviceUI)
        b.grid(row=rowcnt,column=0,sticky=W)
        b = Button(deviceSection, text = "Add Device From File", command = self.openDeviceFromFile)
        b.grid(row=rowcnt,column=1,sticky=W)

        deviceSection.pack(padx=5,pady=5,fill=X,expand=1)
        

        buttonsFrame = Frame(f)
        saveButton = Button(buttonsFrame,text='Save To File',command = self.applyUI)
        saveButton.grid(row=0,column=0,sticky=W)
        loadButton = Button(buttonsFrame,text='Load From File',command = self.loadUI)
        loadButton.grid(row=0,column=1,sticky=W)
        quitButton = Button(buttonsFrame,text='Quit',command = sys.exit)
        quitButton.grid(row=0,column=2,sticky=W)        
        buttonsFrame.pack(fill=X,padx=5,pady=5,expand=1)
        
        f.pack(fill=BOTH,padx=10,pady=10,expand=1)
        outerframe.pack(fill=BOTH,expand=1)
        self.updateDevicesFrame()
        return f

    def applyUI(self):
        for field in self.stringVars.keys():
            updateValueFromStringVar(self,field)
        if self.name == None or len(self.name.strip()) == 0:
            messageBox.showerror("Name missing","Please enter a name into the name field.")
            return
        saveToFileUI(self)


    def loadUI(self):
        fileName = askopenfilename(initialdir = self.dataFolder,defaultextension=".simulator",filetypes=[('simulator files', '.simulator')])
        if fileName == '':
            return
        try:
            self.loadFromFile(fileName,globals=globals())
        except Exception as e:
            msg = "problems loading '" + fileName + '": ' + str(e)
            messageBox.showerror('Simulator load error',msg)

    def updateFromSimulatorInstance(self,simulator):
        Simulator.updateFromSimulatorInstance(self,simulator)
        namesv = getStringVarForField(self,'name')
        namesv.set(simulator.name)
        self.updateDevicesFrame()

    def updateDevicesFrame(self):
        dframe = self.devicesFrame
        for w in dframe.winfo_children():
            w.destroy()
        rowcnt = 0
        for device in self.devices:
            device.buildFrameInSimulatorUI(dframe,rowcnt)
            rowcnt += 1

    def _getUniqueDeviceName(self,prefix="GenericSensorDevice"):
        if self.getDeviceByName(prefix) == None:
            return prefix
        cnt = 1
        while True:
            dname = prefix + str(cnt)
            if self.getDeviceByName(dname) == None:
                return dname
            cnt += 1

    def createDeviceUI(self,device = None):
        try:
            if device == None:
                dev = createDevice(name = self._getUniqueDeviceName())
            else:
                dev = device
            self.addDevice(dev)
            dev.__root__ = self.__root__
            dev.buildUI(master = Toplevel())
            self.updateDevicesFrame()
        except Exception as e:
            messageBox.showerror("Error",str(e))

    def openDeviceFromFile(self):
        fileName = askopenfilename(initialdir = defaultDataFolder,defaultextension=".device",filetypes=[('device files', '.device')])
        if fileName == '':
            return
        try:
            evalstr = getFileContents(fileName)
            device = eval(evalstr)
            device.setLoadFromFileName(fileName)
            self.createDeviceUI(device = device)
        except Exception as e:
            msg = "problems loading '" + fileName + '": ' + str(e)
            messageBox.showerror('Device load error',msg)
            

    def openUI(self):
        self.__root__ = Tk()
        self.__app__ = self.buildUI(self.__root__)
        self.__root__.title("Device Simulator Main")
        #self.__root__.geometry('300x400+100+100')
        if hasattr(self,'load_file_on_init'):
            filename = self.load_file_on_init
            self.loadFromFile(filename,globals=globals())
        self.__root__.mainloop()

    def info(self,message):
        messageBox.showinfo("",message)
        
