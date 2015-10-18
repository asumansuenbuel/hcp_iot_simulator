#
# Dialog to open remote simulator instance
#
# 
# Author: Asuman Suenbuel
# (c) 2015
#

from Tkinter import *
import tkModalDialog
import tkMessageBox as messageBox
from sim_utils import *
import webserver
import urllib2
import json

class OpenRemoteDialog(tkModalDialog.Dialog):

    @staticmethod
    def open(simulator):
        OpenRemoteDialog(simulator.__parent__, simulator = simulator, okText = "Add selected devices", okInitialState = DISABLED)

    def __init__(self,*args,**kwargs):
        if 'simulator' in kwargs:
            self.simulator = kwargs['simulator']
            del kwargs['simulator']
        self.ip = ""
        self.port = webserver.PORT
        addStringVar(self,'ip',"IP-Address/Hostname")
        addStringVar(self,'port',"Port")
        tkModalDialog.Dialog.__init__(self,*args,**kwargs)
        

    def body(self,master):
        f = Frame(master);
        Label(f,text="Open Remote").pack(side=TOP)
        f.pack(side=TOP)
        inputFields = Frame(master)
        createStringInput(self,'ip',inputFields,row=0,column=0,width=25)
        createStringInput(self,'port',inputFields,row=0,column=2,width=6)
        inputFields.pack(side=TOP)
        buttons = Frame(master)
        Button(buttons,text="Get Devices List",command=self.refreshRemoteDevices).grid(sticky=W)
        buttons.pack(side=TOP,anchor=W)
        devicesOuterFrame = Frame(master,relief=SUNKEN,bd=2)
        self.devicesFrame = Frame(devicesOuterFrame)
        Label(self.devicesFrame,text="").grid()
        self.devicesFrame.pack(side=TOP,expand=True,fill=BOTH)
        devicesOuterFrame.pack(side=TOP,expand=True,fill=BOTH,padx=5,pady=5)

    def validate(self):
        print "applying..."
        selectedIndices = []
        index = 0
        for sv in self.deviceCheckbuttonVariables:
            if sv.get() != "0":
                selectedIndices.append(index)
            index += 1
        if len(selectedIndices) == 0:
            messageBox.showinfo("Nothing selected","You did not select any device")
            return 0
        self.selectedIndices = selectedIndices
        return 1

    def apply(self):
        for index in self.selectedIndices:
            url = self.url + '/device/' + str(index)
            try:
                dev = self.simulator.createDevice(url=url)
                self.simulator.addDevice(dev)
            except Exception as e:
                messageBox.showerror("Error",str(e))

        self.simulator.updateDevicesFrame()

    @property
    def url(self):
        ip = getStringVarForField(self,'ip').get().strip()
        if len(ip) == 0:
            raise Exception("please enter an IP-Address/Hostname")
        url = "http://" + ip
        url += ":" + getStringVarForField(self,'port').get()
        return url
            
    def refreshRemoteDevices(self):
        url = ''
        try:
            url = self.url
            response = urllib2.urlopen(url)
            data = json.loads(response.read())
            self.devicesFrame.pack_forget()
            devices = data['devices']
            self.deviceCheckbuttonVariables = []
            if len(devices) == 0:
                Label(self.devicesFrame,text="No devices found on this instance").grid()
                self.okButton.config(state=DISABLED)
            else:
                rowcnt = 0
                for d in devices:
                    sv = StringVar()
                    sv.set(True)
                    self.deviceCheckbuttonVariables.append(sv)
                    Checkbutton(self.devicesFrame,text=d['name'],variable=sv).grid(sticky=W,row=rowcnt,column=1)
                    if d.has_key('isRealDevice'):
                        if d['isRealDevice']:
                            Label(self.devicesFrame,text="real device",background="yellow").grid(sticky=W,row=rowcnt,column=2)

                self.okButton.config(state=NORMAL)

            self.devicesFrame.pack(expand=True,fill=BOTH)
        except Exception as e:
            msg = str(e)
            messageBox.showerror("Error",msg)
            #raise Exception(msg)
