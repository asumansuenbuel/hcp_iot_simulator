# Sensor Simulator
# 
# Author: Asuman Suenbuel
# (c) 2015
#

import time, threading, random, json, sys, urllib3, os
import uuid as uuidlib
from string import Template
from device import *
from thread import *
from sim_utils import *

# --------------------------------------------------------------------------------
def createSensor(*args,**kwargs):
    if 'filename' in kwargs:
        return Sensor.createFromFile(kwargs['filename'])
    return Sensor(*args,**kwargs)
# --------------------------------------------------------------------------------



# ================================================================================
#
# Sensor class
#
# ================================================================================

# The Sensor class is the representation of a sensor emitting simple values
# the (configurable) properties are the following:
#
# - name :
#     the descriptive name of the sensor, e.g. "light", "temperature", etc.
# - unitName :
#     the name of the measurement unit for this sensor (e.g. Lux, Celsius)
# - isFloat :
#     True if the values should be floats, otherwise the value will be integers
# - minValue, maxValue :
#     the range of values that this sensor can emit
# - startValue :
#     the value to start the simulation with
# - varianceSeconds, varianceValue :
#     the maximum change of the values during the given number of
#     seconds; for instance varianceSeconds = 10, varianceValue = 5
#     means that within 10 seconds the sensor value can maximally
#     change by +/- 5. This ensures that the simulator produces
#     somewhat realistic values (e.g. a temperature change of 50
#     degress from 1 second to another would be pretty unlikely...)
# - ndigitsAfterDecimalPoint :
#     for values of type float this specifies the number of digits
#     after the decimal point
#
class Sensor(FilePersistedObject):
    
    @staticmethod
    def createFromFile(filename):
        evalstr = getFileContents(filename)
        obj = eval(evalstr)
        if not isinstance(obj,Sensor):
            raise Exception('object created from file "' + filename + '" is not a Sensor.')
        return obj

    def __init__(self,
                 name,
                 unitName="",
                 isFloat=False,
                 minValue=0,
                 maxValue=50,
                 startValue=None,
                 varianceSeconds=1,
                 varianceValue=1,
                 ndigitsAfterDecimalPoint=2,
                 description=""
             ):
        self.name = name
        self.unitName = unitName
        self.isFloat = isFloat
        self.isInt = not isFloat
        self.minValue = minValue
        self.maxValue = maxValue
        self.startValue = startValue
        self.varianceSeconds = varianceSeconds
        self.varianceValue = varianceValue
        self.ndigitsAfterDecimalPoint = ndigitsAfterDecimalPoint
        self.description = description
        self.device = None
        # internal fields:
        self.validate()
        self.initFilePersistence('sensor')

    def getRandomValueInRange(self,min=None,max=None):
        min = min if min != None else self.minValue
        max = max if max != None else self.maxValue
        if (self.isFloat):
            return round(random.uniform(min,max),self.ndigitsAfterDecimalPoint)
        else:
            return random.randint(min,max)
        
    def nextValue(self,timestamp = None,lastValue=None,lastTimestamp=None,dummyMode=False):
        ts = int(time.time()) if timestamp == None else timestamp
        if dummyMode:
            value = self.getRandomValueInRange()
        else:
            if lastValue == None:
                if self.startValue != None:
                    value = self.startValue
                else:
                    value = self.getRandomValueInRange()
                nextLastValue = value
            else:
                lastTs = lastTimestamp
                if lastTs == None:
                    value = self.getRandomValueInRange()
                    nextLastValue = value
                else:
                    tdiff = ts - lastTs
                    vfactor = float(tdiff)/float(self.varianceSeconds)
                    maxValueDiff = vfactor * self.varianceValue
                    valueDiff = random.uniform(0,maxValueDiff)
                    valueDiff = valueDiff if random.randint(0,1) == 0 else -valueDiff
                    #print "time diff: " + str(tdiff) + " seconds"
                    #print "vfactor: " + str(vfactor)
                    #print "maxValueDiff: " + str(maxValueDiff)
                    #print "valueDiff: " + str(valueDiff)
                    value = lastValue + valueDiff
                    if value < self.minValue or value > self.maxValue:
                        value = lastValue - valueDiff
                        #print "different sign"
                    if value < self.minValue or value > self.maxValue:
                        value = self.getRandomValueInRange()
                        #print "new random value"
                    #print "value: " + str(value)
                    nextLastValue = value
                    
        if self.isFloat:
            if self.ndigitsAfterDecimalPoint != None:
                value = round(value,self.ndigitsAfterDecimalPoint)
        else:
            value = int(round(value))

        nextLastTimestamp = ts
        if not dummyMode:
            res = {'value' : value, 'timestamp' : ts, 'lastValue' : nextLastValue, 'lastTimestamp' : nextLastTimestamp}
        else:
            res = {'value' : value, 'timestamp' : ts}
        return res

    def validate(self):        
        if self.name == None or len(self.name) == 0:
            raise Exception("sensor name must not be empty")
        if not self.minValue < self.maxValue:
            raise Exception("minValue must be less than maxValue")
        if self.startValue != None:
            if not (self.startValue >= self.minValue and self.startValue <= self.maxValue):
                raise Exception("startValue must be in minValue,maxValue range")

    def info(self,message):
        if self.device == None:
            print "info: " + message
        else:
            self.device.info(message)
        
    def __str__(self,indent=''):
        s = indent
        s += "Sensor '" + self.name + "', unit: " + self.unitName
        s += ", minValue: " + str(self.minValue)
        s += ", minValue: " + str(self.maxValue)
        s += ", startValue: " + str(self.startValue)
        s += ", variance: " + str(self.varianceValue) + " in " + str(self.varianceSeconds) + " seconds"
        return s

    def __repr__(self):
        return self.__str__()

    def getPythonConstructorString(self,indent="",standalone=False):
        s = ''
        s += indent + 'createSensor(\n'
        s += indent + '  name = stringUnescape("' + stringEscape(self.name) + '"),\n'
        s += indent + '  unitName = stringUnescape("' + stringEscape(self.unitName) + '"),\n'
        s += indent + '  isFloat = ' + str(self.isFloat) + ',\n'
        s += indent + '  minValue = ' + str(self.minValue) + ',\n'
        s += indent + '  maxValue = ' + str(self.maxValue) + ',\n'
        if self.startValue != None:
            s += indent + '  startValue = ' + str(self.startValue) + ',\n'
        s += indent + '  varianceSeconds = ' + str(self.varianceSeconds) + ',\n'
        s += indent + '  varianceValue = ' + str(self.varianceValue) + ',\n'
        s += indent + '  ndigitsAfterDecimalPoint = ' + str(self.ndigitsAfterDecimalPoint) + ',\n'
        s += indent + '  description = stringUnescape("' + stringEscape(self.description) + '")\n'
        s += indent + ')'
        return s

