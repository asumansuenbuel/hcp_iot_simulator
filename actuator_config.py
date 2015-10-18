# Actuator Configuration
# 
# Author: Asuman Suenbuel
# (c) 2015
#
# This file contains the pre-defined actuators for the simulator and
# the corresponding python function on how to create an instance of
# each of them.

from actuator import *

# --------------------------------------------------------------------------------
#
# customize the set of actuators here:
#

actuatorConstructors = [
    { 'id' : 'lcdDisplay', 'name' : "LCD Display", 'constructor' : lambda *args,**kwargs : createLcdDisplay(*args,**kwargs) },
    { 'id' : 'redLed', 'name' : "Red Led", 'constructor' : lambda *args,**kwargs : createLed(color="red",*args,**kwargs) },
    { 'id' : 'blueLed', 'name' : "Blue Led", 'constructor' : lambda *args,**kwargs : createLed(color="blue",*args,**kwargs) },
    { 'id' : 'greenLed', 'name' : "Green Led", 'constructor' : lambda  *args,**kwargs : createLed(color="green",*args,**kwargs) },
    { 'id' : 'simCtrl', 'name' : "Simulation Controller", 'constructor' : lambda  *args,**kwargs : createSimulationController(*args,**kwargs) }
]

# the fields used in the messageType TO device can be customized here:

messageFields = [
    {
        'name' : 'opcode',
        'type' : 'string',
        'required' : True,
        'defaultValue' : '$actuator_id'
    },{
        'name' : 'operand',
        'type' : 'string',
        'required' : True
    },{
        'name' : 'deviceid',
        'type' : 'string',
        'required' : True,
        'defaultValue' : '$device_id'
    }]

# --------------------------------------------------------------------------------


actuatorIds = map(lambda obj : obj['id'], actuatorConstructors)
actuatorNames = map(lambda obj : obj['name'], actuatorConstructors)

messageFieldNames = map(lambda obj : obj['name'], messageFields)
