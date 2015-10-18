# Actuator Simulator
# 
# Author: Asuman Suenbuel
# (c) 2015
#

import time, threading, random, json, sys, urllib3, os
from device import *
from sim_utils import *

# ================================================================================
#
# Actuator class
#
# ================================================================================

# The actuator class implements a simulated actuator on a sensor
# device, for instance LCD-Display, Led etc.
#
class Actuator(FilePersistedObject):

    @staticmethod
    def createFromFile(filename):
        evalstr = getFileContents(filename)
        obj = eval(evalstr)
        if not isinstance(obj,Actuator):
            raise Exception('object created from file "' + filename + '" is not an Actuator.')
        return obj

    @staticmethod
    def getIdForName(actuatorName):
        import actuator_config
        for aspec in actuator_config.actuatorConstructors:
            if aspec['name'] == actuatorName:
                return aspec['id']
        return None
    
    def __init__(self,name=None,device=None,id="actuator"):
        self.name = name
        self.id = id
        self.device = device
        if device.realDevice != None:
            try:
                device.realDevice.actuatorHooks[id]['init'](device)
            except Exception as e:
                print "[" + str(e) + "]"

    # this is the method where sub-classes implement what to do with a command sent to the
    # actuator. A commandString would, for instance be "on" or "off" for an Led, or a text to
    # display on the LcdDisplay
    def processMessage(self,messageObj):
        if messageObj['opcode'] != self.id:
            return False
        try:
            self.device.realDevice.actuatorHooks[self.id]['processMessage'](self.device,messageObj)
        except Exception as e:
            print "[" + str(e) + "]"

        return True
        

    def removeFromDevice(self):
        if self.device == None:
            return
        if self.device.__class__.__name__.endswith('UI'):
            import tkMessageBox as messageBox
            if messageBox.askyesno('Really remove actuator?','Do you really want to remove the "' + self.name + '" from this device?'):
                self.device.removeActuatorId(self.id)
                self.device.updateActuatorsFrame()
        else:
            self.device.removeActuatorId(self.id)
    
    def __str__(self,indent=""):
        s = 'Generic Actuator'
        return s

    def __repr__(self):
        return self.__str__()

    def info(self,msg):
        if self.device != None:
            self.device.info(msg)
        else:
            print msg

# --------------------------------------------------------------------------------
def createLed(uirunning=False,*args,**kwargs):
    if uirunning:
        from actuator_ui import LedUI
        obj = LedUI(*args,**kwargs)
        return obj
    else:
        return Led(*args,**kwargs)

class Led(Actuator):

    def __init__(self,color,device=None,isOn=False):
        self.color = color if color != None else "red"
        name = color.capitalize() + " Led"
        id = color + "Led"
        self.isOn = isOn
        Actuator.__init__(self,name=name,device=device,id=id)

    def processMessage(self,messageObj):
        if not Actuator.processMessage(self,messageObj):
            return
        text = messageObj['operand']
        ltext = text.lower() if text != None else ""
        self.isOn = (ltext == "on" or text == "true" or text == "1")
        self.info(self.id + " turned " + ("on" if self.isOn else "off"))
        return True

    def __str__(self,indent=""):
        s = ''
        s += indent + self.name + ', status: '
        s += "on" if self.isOn else "off"
        return s
            
        
# --------------------------------------------------------------------------------
def createLcdDisplay(uirunning=False,*args,**kwargs):
    if uirunning:
        from actuator_ui import LcdDisplayUI
        obj = LcdDisplayUI(*args,**kwargs)
        return obj
    else:
        return LcdDisplay(*args,**kwargs)

class LcdDisplay(Actuator):

    def __init__(self,name="LCD Display",device=None):
        name = "LCD Display" if name == None else name
        self.displayText = ""
        Actuator.__init__(self,name=name,device=device,id='lcdDisplay')

    def processMessage(self,messageObj):
        if not Actuator.processMessage(self,messageObj):
            return
        text = messageObj['operand']
        if text != None:
            text = text.replace('\\n','\n')
        self.displayText = text
        self.info('lcdDisplay: displaying text "' + text + '"')
        return True

    def __str__(self,indent=""):
        s = ''
        s += indent + 'LcdDisplay "' + self.name + '", current text: "' + self.displayText + '"'
        return s

# --------------------------------------------------------------------------------

def createSimulationController(uirunning=False,*args,**kwargs):
    return SimulationController(*args,**kwargs)

class SimulationController(Actuator):

    def __init__(self,name=None,device=None):
        name = "Simulation Controller" if name == None else name
        Actuator.__init__(self,name=name,device=device,id='simCtrl')

    def processMessage(self,messageObj):
        if not Actuator.processMessage(self,messageObj):
            return
        command = messageObj['operand']
        self.info("SimulationControl: " + command)
        return True

    def __str__(self,indent=""):
        return "Simulation Controller"


