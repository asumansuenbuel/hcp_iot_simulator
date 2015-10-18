#
# PushService UI
#
# 
# Author: Asuman Suenbuel
# (c) 2015
#


from Tkinter import *
import tkMessageBox as messageBox

from push_service import *
from simulator import *

from sim_utils import *

import sys


# --------------------------------------------------------------------------------
#
# class PushServiceUI: graphical UI for the PushService
#
# --------------------------------------------------------------------------------


class PushServiceUI(PushService):

    def __init__(self,*args,**kwargs):
        PushService.__init__(self,*args,**kwargs)
        self.initStringVars()

    
    def initStringVars(self):
        self.selectedDeviceName = ''
        self.selectedActuatorName = ''
        deviceNames = []
        if self.simulator != None:
            deviceNames = map(lambda d : d.name,self.simulator.devices)
        self.selectedDeviceNameSV = addStringVar(self,'selectedDeviceName','Device',values=deviceNames)
        addStringVar(self,'hcpDeviceId','HCP Device Id')
        addStringVar(self,'messageTypeIdToDevice','HCP Message Type Id (To Device)')
        self.selectedActuatorNameSV = addStringVar(self,'selectedActuatorName','Actuator',values=[''])
        
        self.selectedDeviceNameSV.trace("w",self._updateSelectedDeviceName)
        self.selectedActuatorNameSV.trace("w",self._updateSelectedActuatorName)

        self.messageFieldStringVarNames = [];
        for mname in self.messageFieldNames:
            vname = "__" + mname
            setattr(self,vname,'')
            sv = addStringVar(self,vname,mname)
            self.messageFieldStringVarNames.append(vname)

    
    def buildUI(self,master):
        self.__parent__ = master
        outerframe = Frame(master=master)
        f = Frame(outerframe)

        inputFields = Frame(f)
        rowcnt = 0
        self.selectedDeviceNameOptionMenu = createStringInput(self,'selectedDeviceName',inputFields,rowcnt)
        rowcnt += 1
        self.selectedActuatorNameOptionMenu = createStringInput(self,'selectedActuatorName',inputFields,rowcnt)
        rowcnt += 1
        createStringInput(self,'hcpDeviceId',inputFields,rowcnt,fg='grey')
        rowcnt += 1
        createStringInput(self,'messageTypeIdToDevice',inputFields,rowcnt,fg='grey')
        rowcnt += 1

        inputFields.pack(anchor=W,expand=True)

        payloadFrame = Frame(f,relief=SUNKEN,bd=1)
        Label(payloadFrame,text="Payload",font="-weight bold").grid(row=0,columnspan=3,sticky=W)
        rowcnt = 1
        for vname in self.messageFieldStringVarNames:
            createStringInput(self,vname,payloadFrame,rowcnt)
            rowcnt += 1

        payloadFrame.pack(padx=5,pady=5,fill=X)

        execButtons = Frame(f)

        Button(execButtons,text="Preview Push Message",command=self._previewPushMessage).grid(row=0,column=0)
        Button(execButtons,text="Push Message To HCP",command=self._doPush).grid(row=0,column=1)

        execButtons.pack(fill=BOTH,padx=5,pady=5)


        # output 
        outputFrame = Frame(f)
        outputTitleFrame = Frame(outputFrame)
        l = Label(outputTitleFrame,text="Output",font="-weight bold")
        l.pack(anchor=W,side=LEFT)
        Button(outputTitleFrame,text="Clear",command=self._clearOutput).pack(anchor=W,side=RIGHT)
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
        Button(buttonsFrame,text = "Close", command = lambda : self._closeUI(master)).grid(row=0,column=2,sticky=E)
        buttonsFrame.pack(fill=X,padx=5,pady=5,expand=1)

        
        f.pack(fill=BOTH,padx=10,pady=10,expand=1);
        outerframe.pack(fill=BOTH,expand=1)
        master.title('Push UI')
        pass

    def openAsToplevel(self,openingWindow=None):
        top = Toplevel()
        self.buildUI(master = top)
        #top.protocol("WM_DELETE_WINDOW", lambda : self.closeUI(top))


    def _clearOutput(self):
        self.outputText.delete('1.0',END)

    def _closeUI(self,top=None):
        if top == None:
            top = self.__parent__
        top.destroy()

    def _createPayloadFromStringVars(self):
        payload = {}
        for vname in self.messageFieldStringVarNames:
            infoObj = self.stringVars[vname]
            fieldName = vname[2:]
            value = infoObj['stringVar'].get()
            payload[fieldName] = value
        return payload

    def _doPush(self,dummyMode=False):
        payload = self._createPayloadFromStringVars()
        #str = json.dumps(payload)
        #self.info(str)
        kwargs = payload
        if dummyMode:
            kwargs['dummyMode'] = dummyMode
        self.push(**kwargs)

    def _previewPushMessage(self):
        self._doPush(dummyMode=True)

    def _updateSelectedDeviceName(self,*args):
        sv = getStringVarForField(self,'selectedDeviceName')
        dname = sv.get()
        self.info('device "' + dname + '" selected.')
        if self.simulator == None:
            return
        deviceObj = self.simulator.getDeviceByName(dname)
        if deviceObj == None:
            msg = "Couldn't find device named \"" + dname + "\". Please close and re-open the PushUI."
            messageBox.showerror("device not found",msg)
            return
        self.device = deviceObj
        self.actuator = None
        dsv = getStringVarForField(self,'hcpDeviceId')
        dsv.set(deviceObj.hcpDeviceId)

        msv = getStringVarForField(self,'messageTypeIdToDevice')
        msv.set(deviceObj.messageTypeIdToDevice)
        asv = getStringVarForField(self,'selectedActuatorName')
        asv.set('')
        updateOptionMenuValues(self,'selectedActuatorName',deviceObj.actuatorNames)
        self._updatePayloadFields()

    def _updateSelectedActuatorName(self,*args):
        sv = getStringVarForField(self,'selectedActuatorName')
        aname = sv.get()
        if aname == "":
            return
        self.info('Actuator "' + aname + '" selected.')
        if self.device == None:
            return
        actuatorObj = self.device.getActuatorObjectWithName(aname)
        if actuatorObj == None:
            msg = "Couldn't find actuator \"" + aname + "\" in device \"" + device.name + "\"."
            messageBox.showerror("actuator not found",msg)
            return
        self.actuator = actuatorObj
        self._updatePayloadFields()

    def _updatePayloadFields(self):
        payload = self.createInitialPayload()
        for field,value in payload.iteritems():
            if value == '':
                continue
            vname = "__" + field
            sv = getStringVarForField(self,vname)
            if sv == None:
                continue
            sv.set(value)

        #str = json.dumps(payload)
        #self.info(str)

    
    def info(self,message):
        #print("info: " + message)
        try:
            self.outputText.insert(END,message + "\n")
            self.outputText.see(END)
        except:
            pass
