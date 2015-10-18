# Sensor Device Simulator
# 
# Author: Asuman Suenbuel
# (c) 2015
#

# app-specific imports
from sensor import *
from device_thread import *
from actuator import *
import actuator_config
from sim_utils import *
from real_device import RealDevice

import urllib2,json

# lib imports
import time, threading, random, json, sys, urllib3, os
import uuid as uuidlib
from string import Template

# need to add the current path so that we can support local hcp_config.py files
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

try:
    import hcp_config_saved as configSaved
    attrs = ['hcp_device_id','hcp_oauth_credentials','hcp_message_type_id_from_device','hcp_message_type_id_to_device']
    for attr in attrs:
        if hasattr(configSaved,attr):
            val = getattr(configSaved,attr)
            print "setting attribute '" + attr + "' from hcp_config_saved.py..."
            setattr(config,attr,val)
except ImportError:
    print "hcp_config_saved.py not present."
    pass
    
# --------------------------------------------------------------------------------
def createDevice(*args,**kwargs):
    if 'filename' in kwargs:
        return Device.createFromFile(kwargs['filename'])
    return Device(*args,**kwargs)

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

    def __init__(self,name = "GenericSensorDevice",
                 hcpDeviceId = config.hcp_device_id,
                 hcpOauthCredentials = config.hcp_oauth_credentials,
                 messageTypeId = config.hcp_message_type_id_from_device,
                 messageTypeIdToDevice = config.hcp_message_type_id_to_device,
                 sensors = [],
                 actuatorIds = [],
                 frequencyInSeconds = 10,
                 messageFormat = 'default',
                 description = "",
                 instanceCount = 1, # the number of instances if attached to a simulator
                 uuid = None,
                 pollingFrequency = 5,
                 config = None,
                 realDeviceId = None,
                 url=None):
        self.name = name
        self.sensors=sensors
        self.actuatorIds=actuatorIds
        self.hcpDeviceId = hcpDeviceId
        self.hcpOauthCredentials = hcpOauthCredentials
        self.messageTypeId = messageTypeId
        self.messageTypeIdToDevice = messageTypeIdToDevice
        self.messageFormat = messageFormat
        self.frequencyInSeconds = frequencyInSeconds
        self.description = description
        self.instanceCount = instanceCount
        self.simulator = None
        self.actuatorObjects = []
        self.realDeviceId = realDeviceId
        self.pollingFrequency = pollingFrequency
        self.url = url

        #self.theThread = Thread(self) # for testing start with a single thread; this will go away

        self.threadPool = []
        self.__pollingTimer__ = None
        self._infoBuffer = []
        self._payloadBuffer = []
        self.__infoPollingTimer__ = None

        self.uuid = uuid if uuid != None else str(uuidlib.uuid1())

        if realDeviceId != None:
            self.realDevice = RealDevice(id=realDeviceId)
            self.realDevice.device = self # this invokes the setter in RealDevice Class
            print "device.realDevice is set."
        else:
            self.realDevice = None
        
        self.initFilePersistence('device')
        for sensor in sensors:
            sensor.device = self

        if self.url != None:
            self.initFromUrl()


    # device is a remote device, i.e. it gets all the properties
    # from a device on a different machine. For that to function,
    # a simulator instance must be called with the webserver initiated (-w or -p, --port options)
    # the url must be in the format "http://host:port"
    def initFromUrl(self):
        if self.url == None:
            return
        self.info('initialzing device from url ' + self.url + '...')
        requestUrl = self.url
        try:
            response = urllib2.urlopen(requestUrl)
            data = json.loads(response.read())
            self.info('data loaded from ' + self.url + ", status: ok")
            
            #if data['kind'] == 'simulator':
            #    data = data['devices']

            #if isinstance(data,ListType):
            #    if len(data) == 0:
            #        raise Exception("list must have at least one element")
            #    data = data[0]

            if data['kind'] != 'device':
                raise Exception("wrong kind '" + data['kind'] + "' returned by url, must be a 'device' kind.")

            self.name = data['name']
            self.hcpDeviceId = data['hcpDeviceId']
            self.messageTypeId = data['messageTypeId']
            self.messageTypeIdToDevice = data['messageTypeIdToDevice']
            self.uuid = data['id']
            self.actuatorIds = data['actuatorIds']
            self.messageFormat = data['messageFormat']
            self._isRealDevice = data['isRealDevice']

            sensorObjs = data['sensors']
            for sobj in sensorObjs:
                try:
                    del sobj['kind']
                except:
                    pass
                sensor = self.createSensor(**sobj)
                self.addSensor(sensor)
            
        except Exception as e:
            raise Exception("\n*** something went wrong when trying to access device at " + str(self.url) + "\n*** " + str(e))

    @property
    def instanceCount(self):
        if self.isRealDevice:
            return 1
        if hasattr(self,'_instanceCount'):
            return self._instanceCount
        else:
            self._instanceCount = 1
            return 1

    @instanceCount.setter
    def instanceCount(self,value):
        self._instanceCount = value
            
    @property
    def isRealDevice(self):
        if self.url != None and self._isRealDevice:
            return True
        return hasattr(self,'realDevice') and self.realDevice != None

    def addSensor(self,sensor):
        if not isinstance(sensor,Sensor):
            raise Exception("only objects of type Sensor can be added here")
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

    def createSensor(self,*args,**kwargs):
        return Sensor(*args,**kwargs)


    def _collectSensorValues(self):
        svalues = {}
        for sensor in self.sensors:
            nv = sensor.nextValue(dummyMode=True)
            value = nv['value']
            sname = sensor.name
            svalues[sname] = value
        return svalues
    
    @property
    def availableActuatorIds(self):
        aids = list(actuator_config.actuatorIds)
        for act in self.actuatorIds:
            try:
                aids.remove(act)
            except:
                pass
        return aids

    @property
    def availableActuatorNames(self):
        self._updateActuatorObjects()
        existingIds = map(lambda obj : obj.id,self.actuatorObjects)
        names = []
        for aspec in actuator_config.actuatorConstructors:
            if aspec['id'] in existingIds:
                continue
            names.append(aspec['name'])
        return names
            
    
    def addActuatorId(self,aid):
        try:
            actuator_config.actuatorIds.index(aid)
        except:
            raise Exception('Actuator with id "' + aid + '" is not defined in the system.')
        alreadyContained = False
        try:
            self.actuatorIds.index(aid)
            alreadyContained = True
        except:
            self.actuatorIds.append(aid)
        if alreadyContained:
            raise Exception('Actuator with id "' + aid + '" is already part of this device.')

    def removeActuatorId(self,aid):
        try:
            self.actuatorIds.remove(aid)
            self._updateActuatorObjects()
        except:
            pass
        
    @property
    def actuatorNames(self):
        self._updateActuatorObjects()
        return map(lambda obj : obj.name,self.actuatorObjects)
        
    # this starts the polling thread for the actuators of the device (if the device has actuators)
    def startActuatorThread(self,frequencyInSeconds):
        if length(self.actuatorIds) == 0:
            return
        pass

    def stopActuatorTread(self):
        pass
    
        
    def getDefaultMessageFormat(self):
        msgs = '['
        sep = ""
        for s in self.sensors:
            msg = '{\n'
            msg += '  "sensor" : "' + s.name + '",\n'
            msg += '  "value" : "$' + s.name + '_value",\n'
            msg += '  "timestamp" : $timestamp,\n'
            msg += '  "deviceid" : "$deviceid",\n'
            msg += '  "devicename" : "$devicename"\n'
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

    def threadsAreRunning(self):
        for thread in self.threadPool:
            if thread.threadIsRunning():
                return True
        return False

    # this gets called from the webserver
    # when a post request for the device is received
    def _processRemoteCommand(self,data):
        cmd = data['command']
        if cmd == 'start':
            freq = data['frequencyInSeconds']
            dummyMode = data['dummyMode']
            self.start(frequencyInSeconds=freq,dummyMode=dummyMode)
            return {'message':'simulation started'}
        elif cmd == "stop":
            self.stop()
            return {'message':'simulation stopped'}
        elif cmd == "pause":
            self.pause()
            return {'message':'simulation paused'}
        elif cmd == "saveHcpConfig":
            hcpConfig = data['hcpConfig']
            for field in hcpConfig.keys():
                setattr(self,field,hcpConfig[field])
            self.saveHcpConfig()
            return {'message':'hcpConfig saved'}
        elif cmd == 'startPolling':
            if data.has_key('frequency'):
                self.pollingFrequency = data['frequency']
            self.startPolling()
            return {'message':'polling started'}
        elif cmd == 'stopPolling':
            self.stopPolling()
            return {'message':'polling stopped'}
        else:
            raise Exception('cannot process remote command: ' + str(data))
    
    def dummyStart(self,frequencyInSeconds=5):
        self.start(frequencyInSeconds=frequencyInSeconds,dummyMode=True)
        
    def startRemote(self,frequencyInSeconds,dummyMode=False):
        if self.url == None:
            return
        postUrl = self.url
        data = {'command':'start','frequencyInSeconds' : frequencyInSeconds, 'dummyMode' : dummyMode}
        try:
            postRequest(postUrl,data)
            #req = urllib2.Request(postUrl,data)
            #response = urllib2.urlopen(req)
            #print response.read()
        except Exception as e:
            self.info(str(e))

    def stopRemote(self,paused=False,reset=False):
        if self.url == None:
            return
        postUrl = self.url
        data = {'command':'stop'}
        try:
            postRequest(postUrl,data)
            #req = urllib2.Request(postUrl,data)
            #response = urllib2.urlopen(req)
            #print response.read()
        except Exception as e:
            self.info(str(e))

    def pauseRemote(self):
        self.stopRemote(paused=True)
        
    # starts simulating values using the given frequency
    def start(self,frequencyInSeconds,dummyMode=False):
        if self.url != None:
            self.startRemote(frequencyInSeconds,dummyMode)
            return
        
        self.stop(reset = True)
        self.info("creating and starting " + str(self.instanceCount) + " simulation thread(s)...")

        for i in range(self.instanceCount):
            self.info("starting simulation thread " + str(i) + "...")
            #self.theThread.start(frequencyInSeconds,dummyMode=dummyMode)
            t = self._getThreadObject()
            t.start(frequencyInSeconds,dummyMode=dummyMode)
            self.info("thread " + str(i) + " started.")

        self.info("successfully started " + str(self.instanceCount) + " simulation thread(s).")
        
    def stop(self,paused = False,reset = False):
        if self.url != None:
            self.stopRemote(paused,reset)
            return
        
        #self.theThread.stop(paused=paused)
        for thread in self.threadPool:
            thread.stop(reset=reset)
                      
    def pause(self):
        #self.theThread.pause()
        if self.url != None:
            self.pauseRemote(paused,reset)
            return
        
        for thread in self.threadPool:
            thread.pause()

    @property
    def messageCount(self):
        msgcnt = 0
        for thread in self.threadPool:
            msgcnt += thread.messageCount
        return msgcnt

    @property
    def runningThreadsCount(self):
        cnt = 0
        for thread in self.threadPool:
            if thread.threadIsRunning():
                cnt += 1
        return cnt
    
    @property
    def statInfo(self):
        s = ''
        s += "running threads count:               " + str(self.runningThreadsCount) + '\n'
        s += "total messages sent during this run: " + str(self.messageCount) + '\n'
        return s

    @property
    def payloadBuffer(self):
        bufferContents = self._payloadBuffer
        self._payloadBuffer = []
        return bufferContents
    
    @property
    def infoBuffer(self):
        bufferContents = self._infoBuffer;
        self._infoBuffer = []
        return bufferContents
    
    def info(self,message,tag=None):
        isUIVersion = self.__class__.__name__.endswith('UI')
        self._infoBuffer.append(message)
        if not isUIVersion:
            print message

    def saveHcpConfigRemote(self):
        if self.url == None:
            return
        data = {'command':'saveHcpConfig'}
        hcpConfig = {}
        fields = ['hcpDeviceId','hcpOauthCredentials','messageTypeId','messageTypeIdToDevice']
        for field in fields:
            hcpConfig[field] = getattr(self,field)
        data['hcpConfig'] = hcpConfig
        try:
            postRequest(self.url,data)
        except Exception as e:
            self.info(str(e),"red")
        
    def saveHcpConfig(self):
        if self.url != None:
            self.saveHcpConfigRemote()
            return
        fname = "hcp_config_saved.py"
        s = ''
        s += "hcp_device_id = '" + self.hcpDeviceId + "'\n"
        s += "hcp_oauth_credentials = '" + self.hcpOauthCredentials + "'\n"
        s += "hcp_message_type_id_from_device = '" + self.messageTypeId + "'\n"
        s += "hcp_message_type_id_to_device = '" + self.messageTypeIdToDevice + "'\n"
        saveFile(fname,s)

    def getPythonConstructorString(self,indent="",standalone=False):
        s = ''
        s += indent + 'createDevice(\n'
        s += indent + '  uuid = "' + self.uuid + '",\n'
        s += indent + '  name = stringUnescape("' + stringEscape(self.name) + '"),\n'
        if not self.isRealDevice:
            s += indent + '  actuatorIds = ['
            sep1 = ''
            for aid in self.actuatorIds:
                s += sep1 + 'stringUnescape("' + stringEscape(aid) + '")'
                sep1 = ', '
            s += '],\n'
            s += indent + '  sensors = [\n'
            sep = ''
            for sensor in self.sensors:
                pstr = sensor.getPythonConstructorString(indent = indent + '      ')
                s += sep + pstr
                sep = ',\n'
            s += indent + '\n  ],\n'
        if not standalone:
            s += indent + '  instanceCount = ' + str(self.instanceCount) + ',\n'
        if self.url != None:
            s += indent + '  url = "' + self.url + '",\n'
        s += indent + '  hcpDeviceId = "' + self.hcpDeviceId + '",\n'
        s += indent + '  hcpOauthCredentials = "' + self.hcpOauthCredentials + '",\n'
        s += indent + '  messageTypeId = "' + self.messageTypeId + '",\n'
        s += indent + '  messageTypeIdToDevice = "' + self.messageTypeIdToDevice + '",\n'
        s += indent + '  messageFormat = stringUnescape("' + stringEscape(self.messageFormat) + '"),\n'
        s += indent + '  frequencyInSeconds = ' + str(self.frequencyInSeconds) + ',\n'
        if self.realDeviceId != None:
            s += indent + '  realDeviceId = "' + self.realDeviceId + '",\n'
        s += indent + '  description = stringUnescape("' + stringEscape(self.description) + '")\n'
        s += indent + ')'
        return s

    def nextThreadCounter(self):
        if not hasattr(self,'__threadCounter__'):
            self.__threadCounter__ = 0
        cnt = self.__threadCounter__
        self.__threadCounter__ += 1
        return cnt

    # returns an unused thread object for use in a new simulation run
    # the object can be taken from the pool or a new one is created
    def _getThreadObject(self):
        theThread = None
        for existingThread in self.threadPool:
            if existingThread.threadIsInUse():
                continue
            theThread = existingThread
            self.info('reusing thread object with id "' + theThread.idstr + '"')
        if theThread == None:
            # no thread in the pool found, create a new one and add it to the pool
            theThread = DeviceThread(self)
            self.threadPool.append(theThread)
            self.info('new thread object created with id "' + theThread.idstr + '"')
        theThread.reset()
        return theThread
    
    def __str__(self,indent = ''):
        s = ''
        s += indent + 'Device "' + self.name + '"\n'
        s += indent + '  Sensors:\n'
        for sensor in self.sensors:
            s += sensor.__str__(indent=indent+'    ')
            s += '\n'
        return s


    def __repr__(self):
        return self.__str__()

    def toJson(self):
        obj = {'kind':'device','name':self.name,'id':self.uuid}
        obj['actuatorIds'] = self.actuatorIds
        sobjs = []
        for sensor in self.sensors:
            sobjs.append(sensor.toJson())
        obj['sensors'] = sobjs
        
        for prop in ['hcpDeviceId','messageTypeId','messageTypeIdToDevice','messageFormat']:
            if hasattr(self,prop):
                val = getattr(self,prop)
                obj[prop] = val
        obj['isRealDevice'] = self.isRealDevice
        return obj

    # actuator control

    # checks for messages for this device on HCP
    def _poll_from_hcp(self,processFun=None):
        device = self
        debug_communication = 1
        #self.info("to hcp: " + message)
        if (config.proxy_url == ''):
            http = urllib3.PoolManager()
        else:
            http = urllib3.proxy_from_url(config.proxy_url)

        url='https://iotmms' + config.hcp_account_id + config.hcp_landscape_host + '/com.sap.iotservices.mms/v1/api/http/data/' + str(device.hcpDeviceId)

        # https://iotmmsi806258trial.hanatrial.ondemand.com/com.sap.iotservices.mms/v1/api/http/data/
        
        if debug_communication == 1:
            self.info('url: ' + url)

        headers = urllib3.util.make_headers(user_agent=None)

        # use with authentication
        headers['Authorization'] = 'Bearer ' + device.hcpOauthCredentials
        #headers['Authorization'] = config.hcp_authorization_header
        headers['Content-Type'] = 'application/json;charset=utf-8'

        if processFun == None:
            processFun = lambda payload: self.info(str(payload))
        
        isfun = hasattr(processFun,'__call__')
        
        try:
            r = http.urlopen('GET', url, headers=headers)
            self.info("poll_from_hcp():" + str(r.status))
            if (debug_communication == 1):
                self.info(r.data)
            json_string='{"all_messages":'+(r.data).decode("utf-8")+'}'
            try:
                json_string_parsed=json.loads(json_string)
                # print(json_string_parsed)
                # take care: if multiple messages arrive in 1 payload - their order is last in / first out - so we need to traverse in reverese order
                try:
                    messages_reversed=reversed(json_string_parsed["all_messages"])
                    for single_message in messages_reversed:
                        # print(single_message)
                        payload=single_message["messages"][0]
                        if isfun:
                            processFun(payload)
                except TypeError as te:
                    if debug_communication:
                        self.info("Problem decoding the message " + (r.data).decode("utf-8") + ": " + str(te))
            except ValueError as ve:
                if debug_communication:
                    self.info("Problem decoding the message " + (r.data).decode("utf-8") + ": " + str(ve))
        except Exception as e001:
            self.info(str(e001))

    def _getActuatorObjectWithId(self,id):
        for aobj in self.actuatorObjects:
            if aobj.id == id:
                return aobj
        return None

    def getActuatorObjectWithName(self,name):
        self._updateActuatorObjects()
        for aobj in self.actuatorObjects:
            if aobj.name == name:
                return aobj
        return None

    def _createActuatorObject(self,id):
        isUIVersion = self.__class__.__name__.endswith('UI')
        for aspec in actuator_config.actuatorConstructors:
            if aspec['id'] == id:
                actuatorObject = aspec['constructor'](uirunning=isUIVersion,device=self)
                return actuatorObject
        raise Exception('an actuator with id "' + id + '" is not defined in the system.')

    def _updateActuatorObjects(self):
        for aobj in self.actuatorObjects:
            aobj.removed = True
        for id in self.actuatorIds:
            aobj = self._getActuatorObjectWithId(id)
            if aobj != None:
                aobj.removed = False
                continue
            aobj = self._createActuatorObject(id)
            aobj.removed = False
            self.actuatorObjects.append(aobj)
            self.info('actuator object with id "' + id + '" created.')
        # check for removed ones
        newActuatorObjects = []
        for aobj in self.actuatorObjects:
            if aobj.removed:
                self.info("actuator " + aobj.id + " was removed.")
                continue
            newActuatorObjects.append(aobj)
        self.actuatorObjects = newActuatorObjects

    def _dispatchActuatorMessage(self,payload):
        self.info("dispatching message: " + str(payload))
        self._payloadBuffer.append(payload)
        for aobj in self.actuatorObjects:
            aobj.processMessage(payload)
            
    def actuatorsIteration(self):
        freq = self.pollingFrequency
        self._updateActuatorObjects()
        if len(self.actuatorObjects) == 0:
            #self.info('device has no actuators')
            return
        self._poll_from_hcp(self._dispatchActuatorMessage)
        if self.__pollingTimer__ != None:
            self.__pollingTimer__ = threading.Timer(freq,Device.actuatorsIteration,[self])
            self.__pollingTimer__.start()

    def startPolling(self):
        if self.url != None:
            return postRequest(self.url,{'command':'startPolling','frequency':self.pollingFrequency})
        self.stopPolling()
        freq = self.pollingFrequency
        self.__pollingTimer__ = threading.Timer(2,Device.actuatorsIteration,[self])
        self.__pollingTimer__.start()
        self.info('polling started')


    def stopPolling(self,quiet=True):
        if self.url != None:
            return postRequest(self.url,{'command':'stopPolling'})
        if self.__pollingTimer__ != None:
            self.__pollingTimer__.cancel()
            self.__pollingTimer__ = None
            if not quiet:
                self.info('polling stopped')

    def togglePolling(self):
        if self.pollingIsRunning:
            self.stopPolling()
            return "stopped"
        else:
            self.startPolling()
            return "started"

    @property
    def pollingIsRunning(self):
        if self.url != None:
            url0 = self.url + "/pollingisrunning"
            response = urllib2.urlopen(url0)
            data = json.loads(response.read())
            return data['result']
        return self.__pollingTimer__ != None
        
    # for remote devices: info polling; polls the info messages that are generated by the
    # remote device

    def _processPollInfoData(self,data):
        try:
            messages = data['messages']
            if isinstance(messages,list):
                for msg in messages:
                    self.info("[remote] " + msg,"blue")
            payloads = data['payload']
            if isinstance(payloads,list):
                for payload in payloads:
                    self._dispatchActuatorMessage(payload)
        except Exception as e:
            self.info(str(e),"red")

    def _getSensorValues(self):
        if self.url != None:
            return self._getRemoteSensorValues()
        else:
            return self._collectSensorValues()

    def _getRemoteSensorValues(self):
        url = self.url + "/sensorvalues"
        response = urllib2.urlopen(url)
        data = json.loads(response.read())
        return data
    
    def _pollInfo(self,freq=1):
        infoUrl = self.url + "/info"
        try:
            response = urllib2.urlopen(infoUrl)
            data = json.loads(response.read())
            self._processPollInfoData(data)
            #messages = data['messages']
            #if isinstance(messages,list):
            #    for msg in messages:
            #        self.info(msg)
            #payloads = data['payload']
            #if isinstance(payloads,list):
            #    for payload in payloads:
            #        self._dispatchActuatorMessage(payload)
        except Exception as e:
            self.info(str(e))
        if self.__infoPollingTimer__ != None:
            self.__infoPollingTimer__ = threading.Timer(freq,Device._pollInfo,[self,freq])
            self.__infoPollingTimer__.start()
            
    def startInfoPolling(self,freq=1):
        if self.url == None:
            return
        self.stopInfoPolling()
        self.__infoPollingTimer__ = threading.Timer(1,Device._pollInfo,[self,freq])
        self.__infoPollingTimer__.start()

    def stopInfoPolling(self):
        try:
            self.__infoPollingTimer__.cancel()
        except:
            pass
        finally:
            self.__infoPollingTimer__ = None


    # cleans up, stops all running threads
    def cleanup(self):
        if self.url != None:
            try:
                self.stopPolling()
            except:
                pass
        try:
            self.stopInfoPolling()
        except:
            pass
