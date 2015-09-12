# Sensor Device Simulator
# 

import time, threading, random, json, sys, urllib3,os
import uuid as uuidlib
from string import Template
from sim_utils import *

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
*                                                                                   *
*  2) edit "hcp_config.py" and customize the values according to your HCP settings  *
*                                                                                   *
*  3) restart this script                                                           *
*                                                                                   *
 *********************************************************************************** 
'''
    sys.exit(1)

# --------------------------------------------------------------------------------
def createDevice(*args,**kwargs):
    if 'filename' in kwargs:
        return Device.createFromFile(kwargs['filename'])
    return Device(*args,**kwargs)

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
        self.__lastValue__ = None
        self.__lastTimestamp__ = None
        self.validate()
        self.initFilePersistence('sensor')

    def getRandomValueInRange(self,min=None,max=None):
        min = min if min != None else self.minValue
        max = max if max != None else self.maxValue
        if (self.isFloat):
            return round(random.uniform(min,max),self.ndigitsAfterDecimalPoint)
        else:
            return random.randint(min,max)
        
    def nextValue(self,timestamp = None,dummyMode=False):
        ts = int(time.time()) if timestamp == None else timestamp
        if dummyMode:
            value = self.getRandomValueInRange()
        else:
            if self.__lastValue__ == None:
                if self.startValue != None:
                    value = self.startValue
                else:
                    value = self.getRandomValueInRange()
                self.__lastValue__ = value
            else:
                lastTs = self.__lastTimestamp__
                if lastTs == None:
                    value = self.getRandomValueInRange()
                    self.__lastValue__ = value
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
                    value = self.__lastValue__ + valueDiff
                    #print "value: " + str(value)
                    self.__lastValue__ = value
                    
        if self.isFloat:
            if self.ndigitsAfterDecimalPoint != None:
                value = round(value,self.ndigitsAfterDecimalPoint)
        else:
            value = int(round(value))

        if not dummyMode:
            self.__lastTimestamp__ = ts
        res = { 'value' : value, 'timestamp' : ts}
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
        
    def __str__(self):
        s = "Sensor '" + self.name + "', unit: " + self.unitName
        s += ", minValue: " + str(self.minValue)
        s += ", minValue: " + str(self.maxValue)
        s += ", startValue: " + str(self.startValue)
        s += ", variance: " + str(self.varianceValue) + " in " + str(self.varianceSeconds) + " seconds"
        return s

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

# ================================================================================
#
# Device class
#
# ================================================================================

# The Device class represents the sensor device. It consists of a
# collection of sensors (defined using the Sensor class).
#
class Device(FilePersistedObject):
    
    @staticmethod
    def createFromFile(filename):
        evalstr = getFileContents(filename)
        obj = eval(evalstr)
        if not isinstance(obj,Device):
            raise Exception('object created from file "' + filename + '" is not a Device.')
        return obj

    def __init__(self,name="GenericSensorDevice",
                 hcpDeviceId=config.hcp_device_id,
                 hcpOauthCredentials=config.hcp_oauth_credentials,
                 messageTypeId=config.hcp_message_type_id_from_device,
                 sensors=[],
                 frequencyInSeconds=10,
                 messageFormat='default',
                 description="",
                 instanceCount=1, # the number of instances if attached to a simulator
                 uuid = None):
        self.name = name
        self.sensors=sensors
        self.hcpDeviceId = hcpDeviceId
        self.hcpOauthCredentials = hcpOauthCredentials
        self.messageTypeId = messageTypeId
        self.messageFormat = messageFormat
        self.frequencyInSeconds = frequencyInSeconds
        self.description = description
        self.instanceCount = instanceCount
        self.simulator = None
        self.__timer__ = None
        self.__lastFrequencyInSeconds__ = None
        self.uuid = uuid if uuid != None else str(uuidlib.uuid1())
        self.initFilePersistence('device')
        for sensor in sensors:
            sensor.device = self

    def addSensor(self,sensor):
        if not isinstance(sensor,Sensor):
            raise Exception("only objects of type Sensor can be added to a device")
        for s in self.sensors:
            if s.name == sensor.name:
                raise Exception("you cannot add a sensor with already existing name '" + sensor.name + "' to device '" + self.name + "'.")
        self.sensors.append(sensor)
        sensor.device = self

    def removeSensor(self,sensor):
        try:
            self.sensors.remove(sensor)
            #sensor.device = None
        except:
            pass
        
    def getSensorByName(self,sname):
        for s in self.sensors:
            if s.name == sname:
                return s
        return None

    def getDefaultMessageFormat(self):
        msgs = '['
        sep = ""
        for s in self.sensors:
            msg = '{\n'
            msg += '  "sensor" : "' + s.name + '",\n'
            msg += '  "value" : "$' + s.name + '_value",\n'
            msg += '  "timestamp" : $timestamp,\n'
            msg += '  "deviceid" : "$deviceid"\n'
            msg += '}'
            msgs += sep + msg
            sep = ",\n"
        msgs += ']'
        return msgs

    def getMessageFormat(self):
        if self.messageFormat == 'default':
            return self.getDefaultMessageFormat()
        else:
            return self.messageFormat

    def generateHCPMessage(self,dummyMode=False,messageFormat=None):
        msg = self.getMessageFormat() if messageFormat == None else messageFormat;
        msgTemplate = Template(msg)
        ts = int(time.time())
        evalStr = 'msgTemplate.safe_substitute(timestamp=ts,'
        evalStr += 'deviceid="' + self.uuid + '"'
        for s in self.sensors:
            varname = s.name + '_value'
            valueInfo = s.nextValue(timestamp = ts,dummyMode=dummyMode);
            value = valueInfo['value']
            evalStr += ',' + varname + '=' + str(value)
        evalStr += ')'
        return eval(evalStr)

    def send_to_hcp(self,message):
        debug_communication = 0
        #self.info("to hcp: " + message)
        if (config.proxy_url == ''):
            http = urllib3.PoolManager()
        else:
            http = urllib3.proxy_from_url(config.proxy_url)

        url='https://iotmms' + config.hcp_account_id + config.hcp_landscape_host + '/com.sap.iotservices.mms/v1/api/http/data/' + str(self.hcpDeviceId)
        
        if debug_communication == 1:
            self.info('url: ' + url)

        headers = urllib3.util.make_headers(user_agent=None)

        # use with authentication
        headers['Authorization'] = 'Bearer ' + self.hcpOauthCredentials
        headers['Content-Type'] = 'application/json;charset=utf-8'

        # construct the body
        body = '{ "mode" : "async", "messageType" : "' + str(self.messageTypeId) + '", "messages" : '
        body += message
        body += '}'
        if debug_communication == 1:
            print body

        r = http.urlopen('POST', url, body=body, headers=headers)
        if debug_communication == 1:
            self.info("send_to_hcp():" + str(r.status))
            self.info(r.data)
        else:
            self.info("status: " + str(r.status) + " " + r.data)

    def threadsAreRunning(self):
        return self.__timer__ != None
    
    def startGenerateHCPMessageThread(self,frequencyInSeconds,dummyMode=False):
        msg = self.generateHCPMessage()
        if not dummyMode:
            self.send_to_hcp(msg)
        else:
            self.info("[dummy mode] message to hcp: " + (' '.join(msg.split('\n'))))
        self.__timer__ = threading.Timer(frequencyInSeconds,Device.startGenerateHCPMessageThread,[self,frequencyInSeconds,dummyMode])
        self.__timer__.start()
    
    # starts simulating values using the given frequency
    def start(self,frequencyInSeconds,dummyMode=False):
        global fun
        # if a thread is already running stop it
        self.stop()
        self.info("starting time for sensor '" + self.name + "'...")
        self.__lastFrequencyInSeconds__ = frequencyInSeconds
        #self.__timer__ = threading.Timer(frequencyInSeconds,Sensor.nextValue,[self])
        #self.__timer__.start()
        self.startGenerateHCPMessageThread(frequencyInSeconds,dummyMode);

    def stop(self,paused = False):
        result = False
        if self.__timer__ != None:
            self.__timer__.cancel()
            self.__timer__ = None
            self.info("value emission " + ("paused" if paused else "stopped"))
            result = True
        if not paused:
            self.__lastTimestamp__ = None
            self.__lastValue__ = None

    def pause(self):
        self.stop(paused = True)

    def info(self,message):
        print message

    def getPythonConstructorString(self,indent="",standalone=False):
        s = ''
        s += indent + 'createDevice(\n'
        s += indent + '  uuid = "' + self.uuid + '",\n'
        s += indent + '  name = stringUnescape("' + stringEscape(self.name) + '"),\n'
        s += indent + '  sensors = [\n'
        sep = ''
        for sensor in self.sensors:
            pstr = sensor.getPythonConstructorString(indent = indent + '      ')
            s += sep + pstr
            sep = ',\n'
        s += indent + '\n  ],\n'
        if not standalone:
            s += indent + '  instanceCount = ' + str(self.instanceCount) + ',\n'
        s += indent + '  hcpDeviceId = "' + self.hcpDeviceId + '",\n'
        s += indent + '  hcpOauthCredentials = "' + self.hcpOauthCredentials + '",\n'
        s += indent + '  messageTypeId = "' + self.messageTypeId + '",\n'
        s += indent + '  messageFormat = stringUnescape("' + stringEscape(self.messageFormat) + '"),\n'
        s += indent + '  frequencyInSeconds = ' + str(self.frequencyInSeconds) + ',\n'
        s += indent + '  description = stringUnescape("' + stringEscape(self.description) + '")\n'
        s += indent + ')'
        return s
