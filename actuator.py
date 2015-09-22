# Actuator Simulator
# 
# Author: Asuman Suenbuel
# (c) 2015
#

import time, threading, random, json, sys, urllib3, os
from device import *
from sim_utils import *

sys.path.insert(0,os.getcwd())

try:
    import hcp_config as config
except ImportError as e:
    if os.path.exists('hcp_config_template.py'):
        print '''
 ***********************************************************************************
*                                                                                   *
*  Before the simulator can be used, you need to first configure it as follows:     *
*                                                                                   *
*  1) copy (or rename) the file "hcp_config_template.py" to "hcp_config.py"         *
*     (the hcp_config.py file can also reside in your current working directory)    *
*                                                                                   *
*  2) edit "hcp_config.py" and customize the values according to your HCP settings  *
*                                                                                   *
*  3) restart this script                                                           *
*                                                                                   *
 *********************************************************************************** 
'''
    sys.exit(1)

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
    
    def __init__(self,name=None,thread=None):
        self.name = name
        self.thread = thread

    # this is the method where sub-classes implement what to do with a command sent to the
    # actuator. A commandString would, for instance be "on" or "off" for an Led, or a text to
    # display on the LcdDisplay
    def processCommand(self,commandString):
        pass

    def __str__(self,indent=""):
        s = 'Generic Actuator'
        return s

    def __repr__(self):
        return self.__str__()

# --------------------------------------------------------------------------------

class Led(Actuator):

    def __init__(self,color,thread=None,isOn=False):
        self.color = color if color != None else "red"
        name = color.capitalize() + " Led"
        self.isOn = isOn
        Actuator.__init__(self,name=name,thread=thread)

    def processCommand(self,text):
        ltext = text.lower() if text != None else ""
        self.isOn = (ltext == "on" or text == "true" or text == "1")

    def __str__(self,indent=""):
        s = ''
        s += indent + self.name + ', status: '
        s += "on" if self.isOn else "off"
        return s
            
        
# --------------------------------------------------------------------------------

class LcdDisplay(Actuator):

    def __init__(self,name="LCD Display",thread=None):
        name = "LCD Display" if name == None else name
        self.displayText = ""
        Actuator.__init__(self,name=name,thread=thread)

    def processCommand(self,text):
        self.displayText = text

    def __str__(self,indent=""):
        s = ''
        s += indent + 'LcdDisplay "' + self.name + '", current text: "' + self.displayText + '"'
        return s

# --------------------------------------------------------------------------------

class SimulationController(Actuator):

    def __init__(self,name=None,thread=None):
        name = "Simulation Controller" if name == None else name
        Actuator.__init__(self,name=name,thread=thread)

    def processCommand(self,command):
        
        pass

    def __str__(self,indent=""):
        return "Simulation Controller"

