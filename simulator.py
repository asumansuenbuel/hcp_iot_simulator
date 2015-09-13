# Simulator class definition
# 
# Author: Asuman Suenbuel
# (c) 2015
#

from device import *
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
        self.devices = devices
        self.initFilePersistence(typeSuffix="simulator",dataFolder=".")

    def addDevice(self,device):
        if not isinstance(device,Device):
            raise Exception("only objects of type Device can be added to the simulator")
        '''
        for d in self.devices:
            if d.name == device.name:
                raise Exception("you cannot add a device with already existing name '" +
                                device.name + "' to the simulator.")
        '''
        self.devices.append(device)
        device.simulator = self

    def removeDevice(self,device):
        try:
            self.devices.remove(device)
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
        self.devices = simulator.devices
        for d in self.devices:
            d.simulator = self

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

    def __repr__(self):
        return self.__str__()
