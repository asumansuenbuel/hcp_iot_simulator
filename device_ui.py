# Simulator Device UI
# 
# Author: Asuman Suenbuel
# (c) 2015
#

from device import *
from sensor_ui import *

from Tkinter import *
import tkMessageBox as messageBox
from tkFileDialog import askopenfilename

from device_ui_dialogs import *

from sim_utils import *
import resources
import json,time


# --------------------------------------------------------------------------------
def createDevice(*args,**kwargs):
    if 'filename' in kwargs:
        return Device.createFromFile(kwargs['filename'])
    return DeviceUI(*args,**kwargs)
# --------------------------------------------------------------------------------

class DeviceUI(Device):

    def __init__(self,*args,**kwargs):
        Device.__init__(self,*args,**kwargs)
        self.initStringVars()
        
    def initStringVars(self):
        addStringVar(self,'url','Url')
        addStringVar(self,'uuid','Id')
        addStringVar(self,'name','Name')
        addStringVar(self,'hcpDeviceId','HCP Device Id')
        addStringVar(self,'hcpOauthCredentials','HCP OAuth Credentials')
        addStringVar(self,'messageTypeId','HCP Message Type Id (From Device)')
        addStringVar(self,'messageTypeIdToDevice','HCP Message Type Id (To Device)')
        addStringVar(self,'frequencyInSeconds','Message frequency (seconds)',valueType='int')
        pollingFrequencyVar = addStringVar(self,'pollingFrequency','Polling Frequency',valueType='float')
        instanceCountStringVar = addStringVar(self,'instanceCount','Number of instances in Simulator',valueType='int')
        instanceCountStringVar.trace("w",self._updateInstanceCountFromStringVar)
        instanceCountStringVar.set(int(self.instanceCount))
        self.simulationDummyModeSV = IntVar()
        self.simulationDummyModeSV.set(1)
        # the selectedActuator string var is used in the drop-down for adding actuators:
        self.selectedActuator = None
        selectedActuatorSV = addStringVar(self,'selectedActuator','',values=self.availableActuatorNames)
        pollingFrequencyVar.trace("w",self._updatePollingFrequencyFromStringVar)

    def createSensor(self,*args,**kwargs):
        return SensorUI(*args,**kwargs)
        
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

    def _updatePollingFrequencyFromStringVar(self,*args):
        sv = getStringVarForField(self,'pollingFrequency')
        try:
            num = float(sv.get())
            self.pollingFrequency = num
            self.info("polling frequency set to " + str(num) + " second(s).")
        except ValueError:
            pass

    def debug(self):
        print 'showing values of stringVars:'
        for field in self.stringVars.keys():
            obj = self.stringVars[field]
            print field + ": " + obj['stringVar'].get()

    def updateControlButtons(self,threadsAreRunning=None):
        if len(self.sensors) == 0:
            self.startButton.config(state=DISABLED)
            self.pauseButton.config(state=DISABLED)
            self.stopButton.config(state=DISABLED)
            return

        threadsAreRunning = self.threadsAreRunning() if threadsAreRunning == None else threadsAreRunning
        
        if threadsAreRunning:
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
        if self.isRealDevice:
            labelFrame = Frame(f)
            Label(labelFrame,text="This is a real device.",font="-weight bold",background="yellow").pack()
            labelFrame.pack()
        inputFields = Frame(f)
        rowcnt = 0
        if self.url != None:
            entry = createStringInput(self,'url',inputFields,rowcnt)
            entry.config(state=DISABLED)
            rowcnt += 1
        vv = self.stringVars['uuid']['stringVar']
        Label(inputFields,text = "Id:").grid(row=rowcnt, sticky=W)
        idEntry = Entry(inputFields,width=40,textvariable=vv)
        idEntry.grid(row=rowcnt,column=1,sticky=W)
        #idEntry.insert(0,self.uuid)
        idEntry.config(state=DISABLED)
        rowcnt += 1
        createStringInput(self,'name',inputFields,rowcnt)
        rowcnt += 1
        
        #createStringInput(self,'hcpDeviceId',inputFields,rowcnt)
        #rowcnt += 1
        #createStringInput(self,'hcpOauthCredentials',inputFields,rowcnt)
        #rowcnt += 1
        #createStringInput(self,'messageTypeId',inputFields,rowcnt)
        #rowcnt += 1
        #createStringInput(self,'messageTypeIdToDevice',inputFields,rowcnt)
        #rowcnt += 1

        Button(inputFields,text="Show/Edit HCP Parameters",command=lambda : HCPParametersDialog.open(self)).grid(row=rowcnt)
        
        inputFields.pack(anchor=W,expand=True)

        sensorsOuterFrame = Frame(f,relief=SUNKEN,bd=1)
        rowcnt = 0
        Label(sensorsOuterFrame,text="Onboard Sensors",font="-weight bold").grid(row=rowcnt,sticky=W)
        Button(sensorsOuterFrame,text="Show/Edit Sensors",command=lambda : SensorsDialog.open(self)).grid(row=rowcnt,column=1,sticky=E)
        if False:
            rowcnt += 1
            self.sensorsFrame = Frame(sensorsOuterFrame)
            self.sensorsFrame.grid(row=rowcnt,columnspan=2,pady=5,sticky=W)
            rowcnt += 1
            addSensorButton = Button(sensorsOuterFrame,text="Add New Sensor",command=self.addSensorUI)
            addSensorButton.grid(row=rowcnt,sticky=W,pady=10)
            loadSensorButton = Button(sensorsOuterFrame,text="Add Sensor From File",command=self.addSensorFromFileUI)
            loadSensorButton.grid(row=rowcnt,column=1,sticky=W,pady=10)
        sensorsOuterFrame.pack(padx=5,pady=5,fill=X)

        # ----------------------------------------
        actuatorsOuterFrame = Frame(f,relief=SUNKEN,bd=1)
        Label(actuatorsOuterFrame,text="Actuators",font="-weight bold").pack(anchor=W)
        self.actuatorsFrame = Frame(actuatorsOuterFrame)
        self.actuatorsFrame.pack(fill=X,expand=1)

        if not self.isRealDevice:
            addActuatorFrame = Frame(actuatorsOuterFrame)
            createStringInput(self,'selectedActuator',addActuatorFrame,label="Select Actuator",row=0)
            Button(addActuatorFrame,text="Add Selected Actuator",command=self._addSelectedActuator).grid(row=0,column=3)
            addActuatorFrame.pack(anchor=W)

        actuatorsOuterFrame.pack(padx=5,pady=5,fill=X)
        # ----------------------------------------
        
        messageFormatFrame = Frame(f,relief=SUNKEN,bd=1)
        rowcnt = 0
        Label(messageFormatFrame,text="Message Format",font="-weight bold").pack(anchor=NW,side=LEFT)
        self.editMessageFormatButton = Button(messageFormatFrame,text = 'Show/Edit',command = self._editMessageFormatHandler)
        self.editMessageFormatButton.pack(anchor=NW,side=LEFT)

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

        tc = Frame(controls)
        Label(tc,text="Send Sensor Readings to HCP",font="-weight bold").grid(row=0,sticky=W)
        Button(tc,text="Show/Edit Simulation Parameters",
               command=lambda : SimulationParametersDialog.open(self)).grid(row=0,column=1,sticky=W)
        tc.grid(row=0,columnspan=4,sticky=W)

        freqFrame = Frame(controls)
        rowcnt1 = 0
        if self.simulator != None:
            createStringInput(self,'instanceCount',freqFrame,row=rowcnt1,width = 6)
            rowcnt1 += 1
        createStringInput(self,'frequencyInSeconds',freqFrame,row=rowcnt1,width = 6)
        #freqFrame.grid(row=1,columnspan=3,sticky=W)
        
        self.startButton = Button(controls,text="Start",bg="grey")
        self.startButton.grid(row=2,column=0,sticky=W)
        self.startButton['command'] = self._startSimulationFromUI

        self.pauseButton = Button(controls,text="Pause",bg="grey")
        self.pauseButton.grid(row=2,column=1,sticky=W)
        self.pauseButton['command'] = self._pauseSimulationFromUI

        self.stopButton = Button(controls,text="Stop")
        self.stopButton.grid(row=2,column=2,sticky=W)
        self.stopButton.config(bg="Red")
        self.stopButton['command'] = self._stopSimulationFromUI

        dummyModeCheckButton = Checkbutton(controls,text="Dummy Mode (don't send anything to HCP)",variable=self.simulationDummyModeSV)
        dummyModeCheckButton.grid(row=2,column=3,sticky=W)
        
        controls.pack(padx=5,pady=5,fill=X)

        pollingFrame = Frame(f,relief=SUNKEN,bd=1)
        Label(pollingFrame,text="Poll From HCP",font="-weight bold").grid(row=0,sticky=W)
        self.pollingControlButton = Button(pollingFrame,text="Start/Stop",command=self._togglePolling)
        self.pollingControlButton.grid(row=0,column=1,sticky=E)
        createStringInput(self,'pollingFrequency',pollingFrame,row=0,column=2,width=3)
        self.pollingStatusLabel = Label(pollingFrame,text="status: unknown")
        self.pollingStatusLabel.grid(row=0,column=4)
        pollingFrame.pack(padx=5,pady=5,fill=X)
        
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
        self.outputText.tag_config("blue", foreground="blue")
        self.outputText.tag_config("green", foreground="green")
        self.outputText.tag_config("error", foreground="red")
        xsb.pack(side=BOTTOM, fill=X)
        self.outputText.pack(side=LEFT,fill=BOTH,expand=1)
        xsb.config(command=self.outputText.xview)
        ysb.config(command=self.outputText.yview)
        ysb.pack(side=RIGHT, fill=Y)
        oframe.pack(fill=BOTH,expand=1)

        outputFrame.pack(padx=5,pady=5,fill=BOTH,expand=1)
        
        buttonsFrame = Frame(f)
        Button(buttonsFrame,text = "Apply", command = self.applyUI).grid(row=0,column=0,sticky=W)
        if self.simulator != None and (not self.isRealDevice):
            Button(buttonsFrame,text = "Remove from simulator", command = lambda : self.removeUI(master)).grid(row=0,column=1,sticky=W)
        Button(buttonsFrame,text = "Close", command = lambda : self.closeUI(master)).grid(row=0,column=2,sticky=E)
        buttonsFrame.pack(fill=X,padx=5,pady=5,expand=1)

        f.pack(fill=BOTH,padx=10,pady=10,expand=1);
        outerframe.pack(fill=BOTH,expand=1)
        master.title('Device "' + self.name + '"')
        self.__parent__ = master
        self.updateControlButtons()
        #self.updateSensorsFrame()
        self.updateActuatorsFrame()
        self._updatePollingControlButtonText()
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
        msg = DeviceThread(self).generateHCPMessage(messageFormat=text,dummyMode=True)
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

    def _addSelectedActuator(self):
        sv = getStringVarForField(self,'selectedActuator')
        aname = sv.get()
        if aname == '':
            return
        aid = Actuator.getIdForName(aname)
        if aid == None:
            self.info('couldn\'t add actuator named "' + aname + "'; no id found. Something's gone wrong...")
            return
        self.info('adding actuator with id "' + aid + '"...')
        try:
            self.addActuatorId(aid)
            self.updateActuatorsFrame()
        except Exception as e:
            messageBox.showerror("Error adding actuator",str(e))

    def updateActuatorsFrame(self):
        aframe = self.actuatorsFrame
        for w in aframe.winfo_children():
            w.destroy()
        rowcnt = 0
        self._updateActuatorObjects()
        for aobj in self.actuatorObjects:
            # placeholder
            f = Frame(aframe,relief='sunken',bd=1)
            Label(f,text=aobj.name,width=30).pack(side='left')
            actframe = Frame(f)
            try:
                aobj.initUI(actframe)
            except:
                pass
            actframe.pack(side='left')
            if not self.isRealDevice:
                Button(f,image=resources.getImage('trashCan'),command=aobj.removeFromDevice).pack(side='right')
            f.pack(fill=BOTH,padx=3,pady=3,expand=1)
            rowcnt += 1

        updateOptionMenuValues(self,'selectedActuator',self.availableActuatorNames)
        sv = getStringVarForField(self,'selectedActuator')
        sv.set('')
        
    def _removeActuator(self,id):
        self.info("removing actuator " + id)

    def _processPollInfoData(self,data):
        Device._processPollInfoData(self,data)
        threadsAreRunningNow = data['threadsAreRunning']
        self.updateControlButtons(threadsAreRunning=threadsAreRunningNow)
        #if not hasattr(self,'threadsWereRunningBefore'):
        #    self.threadsWereRunningBefore = not threadsAreRunningNow
        #if threadsAreRunningNow != self.threadsWereRunningBefore:
        #    self.updateControlButtons(threadsAreRunning=threadsAreRunningNow)
        #    self.threadsWereRunningBefore = threadsAreRunningNow

    def startPolling(self):
        Device.startPolling(self)
        try:
            self._updatePollingControlButtonText(pollingIsRunning=False)
        except:
            pass

    def stopPolling(self,quiet=True):
        Device.stopPolling(self,quiet=False)
        try:
            self._updatePollingControlButtonText(pollingIsRunning=False)
        except:
            pass
        
    def _togglePolling(self):
        action = self.togglePolling()

    def _updatePollingControlButtonText(self,pollingIsRunning=None):
        pollingIsRunning = pollingIsRunning if pollingIsRunning == None else self.pollingIsRunning
        btext = "Start"
        ltext = "status: stopped"
        if pollingIsRunning:
            btext = "Stop"
            ltext = "status: running"
        self.pollingControlButton.config(text=btext)
        self.pollingStatusLabel.config(text=ltext)

    def _processPollInfoData(self,data):
        Device._processPollInfoData(self,data)
        pir = data['pollingisrunning']
        self._updatePollingControlButtonText(pollingIsRunning=pir)
        
    def buildFrameInSimulatorUI(self,devicesFrame,rowcnt):
        b = Button(devicesFrame,text=self.name,width=25,textvariable=getStringVarForField(self,'name'))
        b.grid(row=rowcnt,column=0,sticky=W)
        colcnt = 1
        if self.url != None:
            Label(devicesFrame,text="@" + self.url[7:],bd=1,background="yellow").grid(row=rowcnt,column=colcnt)
            colcnt += 1
        if not self.isRealDevice:
            createStringInput(self,'instanceCount',devicesFrame,rowcnt,column=colcnt,width=8,label="   number of instances")
            colcnt += 1
        else:
            Label(devicesFrame,text="Real Device",background="green",bd=1).grid(row=rowcnt,column=colcnt)
            colcnt += 1
        simulatorWindow = devicesFrame.winfo_toplevel()
        #b['command'] = lambda : self.openAsToplevel(simulatorWindow)
        b['command'] = lambda : self.simulator._openOrFocusDeviceWindow(self)

    def openAsToplevel(self,openingWindow=None):
        top = Toplevel()
        top.appObject = self
        self.buildUI(master = top)
        top.protocol("WM_DELETE_WINDOW", lambda : self.closeUI(top))
        if self.url == None:
            self.startPolling()
        else:
            self.startInfoPolling()

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
    
    def addSensorUI(self,sensor=None,dialog=None):
        sname = self._getUniqueSensorName()
        if sensor == None:
            sensor0 = createSensor(name=sname)
        else:
            sensor0 = sensor
        sensor0.device = self
        #sensor0.__root__ = self.__root__
        self.addSensor(sensor0)
        updateTarget = dialog if dialog != None else self
        updateTarget.updateSensorsFrame()

    def addSensorFromFileUI(self,dialog=None):
        fileName = askopenfilename(initialdir = defaultDataFolder,defaultextension=".sensor",filetypes=[('sensor files', '.sensor')])
        if fileName == '':
            return
        try:
            evalstr = getFileContents(fileName)
            sensor = eval(evalstr)
            sensor.setLoadFromFileName(fileName)
            self.addSensorUI(sensor = sensor, dialog = dialog)
        except Exception as e:
            msg = "problems loading '" + fileName + '": ' + str(e)
            messageBox.showerror('Sensor load error',msg)

    def updateSensorsFrame(self):
        pass
        #sframe = self.sensorsFrame
        #for w in sframe.winfo_children():
        #    w.destroy()

        #rowcnt = 0
        #for sensor in self.sensors:
        #    sensor.buildFrameInDeviceUI(sframe,rowcnt)
        #    rowcnt += 1

        self.updateControlButtons()
        self._updateMessageFormatEditor()
            
    def closeUI(self,top=None):
        self.cleanup()
        if top == None:
            try:
                top = self.__parent__
            except:
                pass
        if self.threadsAreRunning():
            if messageBox.askokcancel("Quit", "Simulation thread(s) are still running. Do you want to stop them and close this window?"):
                self._stopSimulationFromUI()
                self.__parent__.update_idletasks()
                time.sleep(1)
            else:
                return
        if top != None:
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

    def info(self,message,tag=None):
        #print("info: " + message)
        Device.info(self,message)
        try:
            self.outputText.insert(END,message + "\n",tag)
            self.outputText.see(END)
        except:
            pass

