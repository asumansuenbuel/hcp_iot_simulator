# Simulator class definition
# 
# Author: Asuman Suenbuel
# (c) 2015
#

from device import *
from real_device import *
from push_service import *
from sim_utils import *

# --------------------------------------------------------------------------------
def createSimulator(*args,**kwargs):
    if 'filename' in kwargs:
        return Simulator.createFromFile(kwargs['filename'])
    return Simulator(*args,**kwargs)
# --------------------------------------------------------------------------------

class Simulator(FilePersistedObject):

    @staticmethod
    def createFromFile(filename):
        evalstr = getFileContents(filename)
        obj = eval(evalstr,globals())
        if not isinstance(obj,Simulator):
            raise Exception('object created from file "' + filename + '" is not a Simulator.')
        return obj
    
    def __init__(self,name="",devices=[]):
        self.name = name
        self.__devices__ = devices
        self.realDeviceId = None
        self.realDeviceObject = None
        self.pollingInterval = 5
        self.initFilePersistence(typeSuffix="simulator",dataFolder=".")

    def postInit(self):
        noPolling = False
        if hasattr(self,'noPolling'):
            noPolling = self.noPolling
        if self.isRunningOnRealDevice and (not noPolling):
            self.realDeviceObject.pollingFrequency = self.pollingInterval
            self.realDeviceObject.startPolling()

    def createDevice(self,*args,**kwargs):
        return Device(*args,**kwargs)

    @property
    def isRunningOnRealDevice(self):
        return len(self.__devices__) == 1 and self.realDeviceObject != None

    @property
    def devices(self):
        # initialize "real device" in case it hasn't been done
        if self.realDeviceId != None and self.realDeviceObject == None:
            rdObj = self.createDevice(realDeviceId=self.realDeviceId)
            self.realDeviceObject = rdObj
            self.addDevice(rdObj)

        return self.__devices__
    
    def addDevice(self,device):
        if not isinstance(device,Device):
            raise Exception("only objects of type Device can be added to the simulator")
        if not (device in self.devices):
            self.__devices__.append(device)
        device.simulator = self

    def removeDevice(self,device):
        try:
            self.__devices__.remove(device)
            #device.simulator = None
        except:
            pass

    def getDeviceByName(self,dname):
        for d in self.devices:
            if d.name == dname:
                return d
        return None
    
    def getPythonConstructorString(self,indent="",standalone=False):
        s = ''
        s += indent + 'createSimulator(\n'
        s += indent + '  name = stringUnescape("' + stringEscape(self.name) + '"),\n'
        s += indent + '  devices = [\n'
        sep = ''
        for device in self.devices:
            pstr = device.getPythonConstructorString(indent = indent + '      ')
            s += sep + pstr
            sep = ',\n'
        s += indent + '\n  ]\n'
        s += indent + ')'
        return s

    def loadFromFile(self,fileName,globals=globals()):
        evalstr = getFileContents(fileName)
        simulator = eval(evalstr,globals)
        self.setLoadFromFileName(fileName)
        self.updateFromSimulatorInstance(simulator)
        
    def updateFromSimulatorInstance(self,simulator):
        self.name = simulator.name
        self.__devices__ = simulator.devices
        for d in self.devices:
            d.simulator = self

    def cleanupOnExit(self):
        for d in self.devices:
            try:
                d.cleanup()
                print "polling stop on device \"" + d.name + "\"."
            except:
                pass
            try:
                d.stop()
            except:
                pass


    def info(self,message):
        print "info: " + message

    def __str__(self):
        s = ''
        s += 'Simulator '
        if self.name != None and self.name.strip() != "":
            s += '"' + self.name + '"'
        s += '\n'
        if len(self.devices) == 0:
            s += '  no devices'
        else:
            s += '  Devices:\n'
            for d in self.devices:
                s += d.__str__(indent='    ')
        return s

    def toJson(self):
        obj = {'kind':'simulator','name':str(self.name)}
        dobjs = []
        for d in self.devices:
            dobjs.append(d.toJson())
        obj['devices'] = dobjs
        return obj
    
    def __repr__(self):
        return self.__str__()
