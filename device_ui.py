# Simular Device and Sensor UI
# 
# Author: Asuman Suenbuel
# (c) 2015
#

from Tkinter import *
import tkMessageBox as messageBox
from tkFileDialog import askopenfilename
from device import *
from sim_utils import *
import json,time
# --------------------------------------------------------------------------------
def createDevice(*args,**kwargs):
    if 'filename' in kwargs:
        return Device.createFromFile(kwargs['filename'])
    return DeviceUI(*args,**kwargs)

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
        Button(buttonsFrame,text = "Apply", command = lambda : self.applyUI(master)).grid(row=0,column=0,sticky=W)
        if self.device != None:
            Button(buttonsFrame,text = "Remove from device", command = lambda : self.removeUI(master)).grid(row=0,column=1,sticky=W)
        Button(buttonsFrame,text = "Cancel", command = lambda : self.closeUI(master)).grid(row=0,column=2,sticky=E)
        buttonsFrame.pack(fill=X,padx=5,pady=5,expand=1)

        f.pack(fill=BOTH,padx=10,pady=10,expand=1);
        outerframe.pack(fill=BOTH,expand=1)
        master.title("Sensor \"" + self.name + "\"")

    def openAsToplevel(self):
        top = Toplevel()
        top.appObject = self
        self.buildUI(master = top)
        #self.__root__.wait_window(top)
                   
    def buildFrameInDeviceUI(self,sensorsFrame,rowcnt):
        b = Button(sensorsFrame,text=self.name,bg="lightblue",width=25)
        b.grid(row=rowcnt,column=0,sticky=W)
        b['command'] = self.openAsToplevel

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
            self.device.updateSensorsFrame()
            self.closeUI(top)
    
    def closeUI(self,top):
        top.destroy()


# --------------------------------------------------------------------------------

class DeviceUI(Device):

    def __init__(self,*args,**kwargs):
        Device.__init__(self,*args,**kwargs)
        self.initStringVars()

    
    def initStringVars(self):
        addStringVar(self,'uuid','Id')
        addStringVar(self,'name','Name')
        addStringVar(self,'hcpDeviceId','HCP Device Id')
        addStringVar(self,'hcpOauthCredentials','HCP OAuth Credentials')
        addStringVar(self,'messageTypeId','HCP Message Type Id (From Device)')
        addStringVar(self,'frequencyInSeconds','Message frequency (seconds)',valueType='int')
        instanceCountStringVar = addStringVar(self,'instanceCount','Number of instances in Simulator',valueType='int')
        instanceCountStringVar.trace("w",self._updateInstanceCountFromStringVar)
        instanceCountStringVar.set(int(self.instanceCount))
        self.simulationDummyModeSV = IntVar()
        self.simulationDummyModeSV.set(1)

    def _setMessageFormatFromSV(self,*args):
        print "args in _setMessageFormatFromSV: " + str(args)

    def _updateInstanceCountFromStringVar(self,*args):
        sv = getStringVarForField(self,'instanceCount')
        try:
            num = int(sv.get())
        except ValueError:
            num = 1
        self.instanceCount = num
        #print "instanceCount updated: " + str(self.instanceCount)

    def debug(self):
        print 'showing values of stringVars:'
        for field in self.stringVars.keys():
            obj = self.stringVars[field]
            print field + ": " + obj['stringVar'].get()

    def updateControlButtons(self):
        if len(self.sensors) == 0:
            self.startButton.config(state=DISABLED)
            self.pauseButton.config(state=DISABLED)
            self.stopButton.config(state=DISABLED)
            return

        if self.threadsAreRunning():
            self.startButton.config(state=DISABLED)
            self.pauseButton.config(state=ACTIVE)
            self.stopButton.config(state=ACTIVE)
        else:
            self.startButton.config(state=ACTIVE)
            self.pauseButton.config(state=DISABLED)
            self.stopButton.config(state=DISABLED)
            
    
    def buildUI(self,master):
        #self.initStringVars()
        outerframe = Frame(master=master)
        f = Frame(outerframe)
        inputFields = Frame(f)
        rowcnt = 0
        vv = self.stringVars['uuid']['stringVar']
        Label(inputFields,text = "Id:").grid(row=rowcnt, sticky=W)
        rowcnt += 1
        idEntry = Entry(inputFields,width=40,textvariable=vv)
        idEntry.grid(row=0,column=1,sticky=W)
        #idEntry.insert(0,self.uuid)
        idEntry.config(state=DISABLED)
        createStringInput(self,'name',inputFields,rowcnt)
        rowcnt += 1
        createStringInput(self,'hcpDeviceId',inputFields,rowcnt)
        rowcnt += 1
        createStringInput(self,'hcpOauthCredentials',inputFields,rowcnt)
        rowcnt += 1
        createStringInput(self,'messageTypeId',inputFields,rowcnt)
        rowcnt += 1

        inputFields.pack(anchor=W,expand=True)

        sensorsOuterFrame = Frame(f,relief=SUNKEN,bd=1)
        rowcnt = 0
        Label(sensorsOuterFrame,text="Onboard Sensors",font="-weight bold").grid(row=rowcnt,sticky=W)
        rowcnt += 1
        self.sensorsFrame = Frame(sensorsOuterFrame)
        self.sensorsFrame.grid(row=rowcnt,columnspan=2,pady=5,sticky=W)
        rowcnt += 1
        addSensorButton = Button(sensorsOuterFrame,text="Add New Sensor",command=self.addSensorUI)
        addSensorButton.grid(row=rowcnt,sticky=W,pady=10)
        loadSensorButton = Button(sensorsOuterFrame,text="Add Sensor From File",command=self.addSensorFromFileUI)
        loadSensorButton.grid(row=rowcnt,column=1,sticky=W,pady=10)
        sensorsOuterFrame.pack(padx=5,pady=5,fill=X)

        messageFormatFrame = Frame(f,relief=SUNKEN,bd=1)
        rowcnt = 0
        Label(messageFormatFrame,text="Message Format",font="-weight bold").pack(anchor=W)
        self.editMessageFormatButton = Button(messageFormatFrame,text = 'Show/Edit',command = self._editMessageFormatHandler)
        self.editMessageFormatButton.pack(anchor=W)

        self.messageFormatEditorFrame = Frame(messageFormatFrame)
        mframe = Frame(self.messageFormatEditorFrame,bd=2,relief=SUNKEN)
        ysb = Scrollbar(mframe, orient=VERTICAL)
        self.messageFormatEditor = Text(mframe,yscrollcommand=ysb.set,height=10,width=80)
        self.messageFormatEditor.pack(side=LEFT,fill=BOTH,expand=1)
        ysb.config(command=self.messageFormatEditor.yview)
        ysb.pack(side=RIGHT, fill=Y)
        mframe.pack(fill=BOTH,expand=1,padx=10,pady=10)
        buttons = Frame(self.messageFormatEditorFrame)
        Button(buttons,text = 'Apply', command = self._applyMessageFormatEditor).grid(row=0,column=0,sticky=W)
        Button(buttons,text = 'Reset To Default', command = self._resetMessageFormatToDefault).grid(row=0,column=1,sticky=W)
        Button(buttons,text = 'Check Message Format', command = self._testMessageFormat).grid(row=0,column=2,sticky=W)
        buttons.pack(anchor=W)

        #self.messageFormatEditorFrame.pack(fill=BOTH,expand=1,padx=5,pady=5)
        messageFormatFrame.pack(padx=5,pady=5,fill=BOTH,expand=1)
        
        controls = Frame(f,relief=SUNKEN,bd=1)

        Label(controls,text="Simulation Controls",font="-weight bold").grid(row=0,columnspan=3,sticky=W)

        freqFrame = Frame(controls)
        rowcnt1 = 0
        if self.simulator != None:
            createStringInput(self,'instanceCount',freqFrame,row=rowcnt1,width = 6)
            rowcnt1 += 1
        createStringInput(self,'frequencyInSeconds',freqFrame,row=rowcnt1,width = 6)
        freqFrame.grid(row=1,columnspan=3)
        
        self.startButton = Button(controls,text="Start",bg="grey")
        self.startButton.grid(row=2,column=0)
        self.startButton['command'] = self._startSimulationFromUI

        self.pauseButton = Button(controls,text="Pause",bg="grey")
        self.pauseButton.grid(row=2,column=1)
        self.pauseButton['command'] = self._pauseSimulationFromUI

        self.stopButton = Button(controls,text="Stop")
        self.stopButton.grid(row=2,column=2)
        self.stopButton.config(bg="Red")
        self.stopButton['command'] = self._stopSimulationFromUI

        dummyModeCheckButton = Checkbutton(controls,text="Dummy Mode (don't send anything to HCP)",variable=self.simulationDummyModeSV)
        dummyModeCheckButton.grid(row=2,column=3)
        
        controls.pack(padx=5,pady=5,fill=X)

        outputFrame = Frame(f)
        outputTitleFrame = Frame(outputFrame)
        l = Label(outputTitleFrame,text="Output",font="-weight bold")
        l.pack(anchor=W,side=LEFT)
        Button(outputTitleFrame,text="Clear",command=self._clearOutput).pack(anchor=W,side=RIGHT)
        Button(outputTitleFrame,text="Stats",command=self._showStats).pack(anchor=W,side=RIGHT)
        outputTitleFrame.pack(anchor=W,fill=X,expand=1)

        oframe = Frame(outputFrame,bd=2,relief=SUNKEN)

        xsb = Scrollbar(oframe, orient=HORIZONTAL)
        ysb = Scrollbar(oframe, orient=VERTICAL)
        self.outputText = Text(oframe,xscrollcommand=xsb.set,yscrollcommand=ysb.set,height=10,width=80,wrap=NONE)
        xsb.pack(side=BOTTOM, fill=X)
        self.outputText.pack(side=LEFT,fill=BOTH,expand=1)
        xsb.config(command=self.outputText.xview)
        ysb.config(command=self.outputText.yview)
        ysb.pack(side=RIGHT, fill=Y)
        oframe.pack(fill=BOTH,expand=1)

        outputFrame.pack(padx=5,pady=5,fill=BOTH,expand=1)
        
        buttonsFrame = Frame(f)
        Button(buttonsFrame,text = "Apply", command = self.applyUI).grid(row=0,column=0,sticky=W)
        if self.simulator != None:
            Button(buttonsFrame,text = "Remove from simulator", command = lambda : self.removeUI(master)).grid(row=0,column=1,sticky=W)
        Button(buttonsFrame,text = "Close", command = lambda : self.closeUI(master)).grid(row=0,column=2,sticky=E)
        buttonsFrame.pack(fill=X,padx=5,pady=5,expand=1)

        f.pack(fill=BOTH,padx=10,pady=10,expand=1);
        outerframe.pack(fill=BOTH,expand=1)
        master.title('Device "' + self.name + '"')
        self.__parent__ = master
        self.updateControlButtons()
        self.updateSensorsFrame()
        return f

    def _clearOutput(self):
        self.outputText.delete('1.0',END)

    def _showStats(self):
        s = self.statInfo
        self.info(s)
        self.__parent__.after(0,self._showStatsInAlert)

    def _showStatsInAlert(self):
        messageBox.showinfo("Simulation stats",self.statInfo)
        
    def _updateMessageFormatEditor(self):
        t = self.messageFormatEditor
        t.delete('1.0',END)
        t.insert('1.0',self.getMessageFormat())

    def _resetMessageFormatToDefault(self):
        text = self.messageFormatEditor.get('1.0',END)
        if self.messageFormat == 'default' and (text == self.getMessageFormat()):
            return
        if messageBox.askyesno("Reset to default?", "Do you really want to reset the message format to its default value? All your changes will be lost."):
            self.messageFormat = 'default'
            self._updateMessageFormatEditor()

    def _applyMessageFormatEditor(self):
        text = self.messageFormatEditor.get('1.0',END)
        if text.strip() == 'default':
            self.messageFormat = 'default'
        else:
            self.messageFormat = text

    def _testMessageFormat(self):
        text = self.messageFormatEditor.get('1.0',END)
        msg = Thread(self).generateHCPMessage(messageFormat=text,dummyMode=True)
        self.info("generated example message:")
        self.info(msg)
        infomsg = "Message format check succeeded."
        try:
            json.loads(msg)
            self.info("JSON check: ok")
            messageBox.showinfo("check succeeded",infomsg)
        except Exception as e:
            self.info("JSON check failed!")
            self.info(str(e))
            infomsg = "Message format check failed: " + str(e)
            messageBox.showerror("check failed",infomsg)
            
    def _editMessageFormatHandler(self):
        b = self.editMessageFormatButton
        if self.messageFormatEditorFrame.winfo_manager() == "": # means it is not showing (packed)
            self.messageFormatEditorFrame.pack(fill=BOTH,expand=1)
            self._updateMessageFormatEditor()
            b['text'] = "Hide"
        else:
            self.messageFormatEditorFrame.pack_forget()
            b['text'] = "Show/Edit"
        

    def buildFrameInSimulatorUI(self,devicesFrame,rowcnt):
        b = Button(devicesFrame,text=self.name,bg="lightblue",width=25)
        b.grid(row=rowcnt,column=0,sticky=W)
        createStringInput(self,'instanceCount',devicesFrame,rowcnt,column=1,width=8,label="   number of instances")
        simulatorWindow = devicesFrame.winfo_toplevel()
        b['command'] = lambda : self.openAsToplevel(simulatorWindow)

    def openAsToplevel(self,openingWindow=None):
        top = Toplevel()
        top.appObject = self
        self.buildUI(master = top)
        top.protocol("WM_DELETE_WINDOW", lambda : self.closeUI(top))
        #top.geometry('+5+242')
        #top.wait_visibility(top)
        #print str(openingWindow.winfo_geometry())

    def hasWindowOpen(self):
        try:
            dwins = self.simulator._getAllDeviceWindows()
            for w in dwins:
                if hasattr(w,'appObject') and w.appObject == self:
                    return True
            return False
        except:
            return False
        
    def _startSimulationFromUI(self):
        freq = float(self.stringVars['frequencyInSeconds']['stringVar'].get())
        dummyMode = self.simulationDummyModeSV.get() == 1
        if dummyMode:
            self.info("starting simulation in dummy mode...")
        else:
            self.info("starting simulation in real mode...")
        #print(freq)
        self.start(freq,dummyMode)
        self.updateControlButtons()

    def _stopSimulationFromUI(self):
        self.stop();
        self.updateControlButtons();

    def _pauseSimulationFromUI(self):
        self.pause();
        self.updateControlButtons();
        
    def _getUniqueSensorName(self,prefix="GenericSensor"):
        if self.getSensorByName(prefix) == None:
            return prefix
        cnt = 1
        while True:
            sname = prefix + str(cnt)
            if self.getSensorByName(sname) == None:
                return sname
            cnt += 1
    
    def addSensorUI(self,sensor=None):
        sname = self._getUniqueSensorName()
        if sensor == None:
            sensor0 = createSensor(name=sname)
        else:
            sensor0 = sensor
        sensor0.device = self
        #sensor0.__root__ = self.__root__
        self.addSensor(sensor0)
        self.updateSensorsFrame()

    def addSensorFromFileUI(self):
        fileName = askopenfilename(initialdir = defaultDataFolder,defaultextension=".sensor",filetypes=[('sensor files', '.sensor')])
        if fileName == '':
            return
        try:
            evalstr = getFileContents(fileName)
            sensor = eval(evalstr)
            sensor.setLoadFromFileName(fileName)
            self.addSensorUI(sensor = sensor)
        except Exception as e:
            msg = "problems loading '" + fileName + '": ' + str(e)
            messageBox.showerror('Sensor load error',msg)

    def updateSensorsFrame(self):
        sframe = self.sensorsFrame
        for w in sframe.winfo_children():
            w.destroy()

        rowcnt = 0
        for sensor in self.sensors:
            sensor.buildFrameInDeviceUI(sframe,rowcnt)
            rowcnt += 1

        self.updateControlButtons()
        self._updateMessageFormatEditor()
            
    def closeUI(self,top=None):
        if top == None:
            top = self.__parent__
        if self.threadsAreRunning():
            if messageBox.askokcancel("Quit", "Simulation thread(s) are still running. Do you want to stop them and close this window?"):
                self._stopSimulationFromUI()
                self.__parent__.update_idletasks()
                time.sleep(1)
            else:
                return
        top.destroy()

    def applyUI(self):
        for field in self.stringVars.keys():
            updateValueFromStringVar(self,field)
        saveToFileUI(self,standalone=True)

    def removeUI(self,top):
        title = "Remove device?"
        msg = "Do you really want to remove this device from the simulator?"
        if messageBox.askyesno(title,msg):
            self.simulator.removeDevice(self)
            self.simulator.updateDevicesFrame()
            self.closeUI(top)

    def _closeUI(self,top):
        top.destroy()

    def info(self,message):
        #print("info: " + message)
        self.outputText.insert(END,message + "\n")
        self.outputText.see(END)

