from Tkinter import *
import tkModalDialog
from sim_utils import *

class HCPParametersDialog(tkModalDialog.Dialog):

    @staticmethod
    def open(device):
        HCPParametersDialog(device.__parent__,device=device)

    def __init__(self,*args,**kwargs):
        if 'device' in kwargs:
            self.device = kwargs['device']
            del kwargs['device']
        tkModalDialog.Dialog.__init__(self,*args,**kwargs)

    def body(self,master):
        device = self.device
        inputFields = master
        rowcnt = 0
        createStringInput(device,'hcpDeviceId',inputFields,rowcnt)
        rowcnt += 1
        createStringInput(device,'hcpOauthCredentials',inputFields,rowcnt)
        rowcnt += 1
        createStringInput(device,'messageTypeId',inputFields,rowcnt)
        rowcnt += 1
        createStringInput(device,'messageTypeIdToDevice',inputFields,rowcnt)
        rowcnt += 1

class SensorsDialog(tkModalDialog.Dialog):

    @staticmethod
    def open(device):
        SensorsDialog(device.__parent__,device=device,isModal=False)

    def __init__(self,*args,**kwargs):
        if 'device' in kwargs:
            self.device = kwargs['device']
            del kwargs['device']
        tkModalDialog.Dialog.__init__(self,*args,**kwargs)

    def body(self,master):
        sensorsOuterFrame = master
        rowcnt = 1
        Label(sensorsOuterFrame,text="Onboard Sensors",font="-weight bold").grid(row=rowcnt,sticky=W)
        rowcnt += 1
        self.sensorsFrame = Frame(sensorsOuterFrame)
        self.sensorsFrame.grid(row=rowcnt,columnspan=2,pady=5,sticky=W)
        rowcnt += 1
        addSensorButton = Button(sensorsOuterFrame,text="Add New Sensor",
                                 command=lambda : self.device.addSensorUI(dialog=self))
        addSensorButton.grid(row=rowcnt,sticky=W,pady=10)
        loadSensorButton = Button(sensorsOuterFrame,text="Add Sensor From File",
                                  command=lambda : self.device.addSensorFromFileUI(dialog=self))
        loadSensorButton.grid(row=rowcnt,column=1,sticky=W,pady=10)
        self.updateSensorsFrame()

    def updateSensorsFrame(self):
        sframe = self.sensorsFrame
        for w in sframe.winfo_children():
            w.destroy()

        rowcnt = 0
        for sensor in self.device.sensors:
            sensor.buildFrameInDeviceUI(sframe,rowcnt,dialog=self)
            rowcnt += 1

        self.device.updateControlButtons()
        self.device._updateMessageFormatEditor()
            

class SimulationParametersDialog(tkModalDialog.Dialog):

    @staticmethod
    def open(device):
        SimulationParametersDialog(device.__parent__,device=device)

    def __init__(self,*args,**kwargs):
        if 'device' in kwargs:
            self.device = kwargs['device']
            del kwargs['device']
        tkModalDialog.Dialog.__init__(self,*args,**kwargs)

    def body(self,master):
        device = self.device
        if device.simulator != None:
            createStringInput(device,'instanceCount',master,row=0,width = 6)
        createStringInput(device,'frequencyInSeconds',master,row=1,width = 6)


