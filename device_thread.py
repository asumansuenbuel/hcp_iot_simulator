# Simulation thread
# 
# Author: Asuman Suenbuel
# (c) 2015
#

import time, threading, random, json, sys, urllib3, os
import uuid as uuidlib
from string import Template
from device import *
from sim_utils import *

urllib3.disable_warnings()

# ================================================================================
#
# DeviceThread class
#
# ================================================================================

# A DeviceThread instance represents a process that simulates a device emitting sensor values
# to HCP. A DeviceThread belongs to a device and is a transient object; it only exists while the
# simulation is running. It's life-cycle (start,stop,pause) is controlled by the device

class DeviceThread:

    def __init__(self,device):
        self.device = device
        self.id = device.nextThreadCounter()
        self.reset()

    @property
    def idstr(self):
        s = '00000000' + hex(self.id)[2:]
        l = len(s)
        return s[l-8:]

    @property
    def uuid(self):
        return self.device.uuid + "-" + self.idstr

    def reset(self):
        self.__timer__ = None
        self.__lastValue__ = None
        self.__lastTimestamp__ = None
        self.__messageCounter__ = 0

    def send_to_hcp(self,message):
        device = self.device
        debug_communication = 0
        #self.info("to hcp: " + message)
        if (config.proxy_url == ''):
            http = urllib3.PoolManager()
        else:
            http = urllib3.proxy_from_url(config.proxy_url)

        url='https://iotmms' + config.hcp_account_id + config.hcp_landscape_host + '/com.sap.iotservices.mms/v1/api/http/data/' + str(device.hcpDeviceId)
        
        if debug_communication == 1:
            self.info('url: ' + url)

        headers = urllib3.util.make_headers(user_agent=None)

        # use with authentication
        headers['Authorization'] = 'Bearer ' + device.hcpOauthCredentials
        headers['Content-Type'] = 'application/json;charset=utf-8'

        # construct the body
        body = '{ "mode" : "async", "messageType" : "' + str(device.messageTypeId) + '", "messages" : '
        body += message
        body += '}'
        if debug_communication == 1:
            print body
        else:
            self.info("[" + self.idstr + "] message to hcp: " + (' '.join(message.split('\n'))))

        r = http.urlopen('POST', url, body=body, headers=headers)
        if debug_communication == 1:
            self.info("send_to_hcp():" + str(r.status))
            self.info(r.data)
        else:
            self.info("[" + self.idstr + "] response status: " + str(r.status) + " " + r.data)

    def generateHCPMessage(self,dummyMode=False,messageFormat=None):
        device = self.device
        msg = device.getMessageFormat() if messageFormat == None else messageFormat;
        msgTemplate = Template(msg)
        ts = int(time.time())
        evalStr = 'msgTemplate.safe_substitute(timestamp=ts,'
        evalStr += 'deviceid="' + self.uuid + '",'
        evalStr += 'devicename="' + self.device.name + '-' + self.idstr + '"'
        for s in device.sensors:
            varname = s.name + '_value'
            valueInfo = s.nextValue(timestamp = ts,lastValue=self.__lastValue__,lastTimestamp=self.__lastTimestamp__,dummyMode=dummyMode);
            value = valueInfo['value']
            if not dummyMode:
                self.__lastValue__ = valueInfo['lastValue']
                self.__lastTimestamp__ = valueInfo['lastTimestamp']
            evalStr += ',' + varname + '=' + str(value)
        evalStr += ')'
        return eval(evalStr)

    def startGenerateHCPMessageThread(self,frequencyInSeconds,dummyMode=False):
        device = self.device
        msg = self.generateHCPMessage()
        if not dummyMode:
            self.send_to_hcp(msg)
        else:
            self.info("[" + self.idstr + "] message to dummy: " + (' '.join(msg.split('\n'))))
        self.__messageCounter__ += 1
        if self.__timer__ == None:
            self.info("[" + self.idstr + "] no new cycle started, because simulation has been stopped")
            return
        self.__timer__ = threading.Timer(device.frequencyInSeconds,DeviceThread.startGenerateHCPMessageThread,[self,device.frequencyInSeconds,dummyMode])
        self.__timer__.start()
    
    def start(self,frequencyInSeconds,dummyMode=False):
        # if a thread is already running stop it
        self.stop()
        self.info("[" + self.idstr + "] starting simulation thread with frequency " + str(frequencyInSeconds))
        self.__lastFrequencyInSeconds__ = frequencyInSeconds
        #self.__timer__ = threading.Timer(frequencyInSeconds,Sensor.nextValue,[self])
        #self.__timer__.start()
        self.__timer__ = threading.Timer(0,DeviceThread.startGenerateHCPMessageThread,[self,self.device.frequencyInSeconds,dummyMode])
        self.__timer__.start()
        #self.startGenerateHCPMessageThread(frequencyInSeconds,dummyMode);

    def stop(self,paused=False,reset=False):
        if self.__timer__ != None:
            self.__timer__.cancel()
            self.__timer__ = None
            self.info("[" + self.idstr + "] simulation " + ("paused" if paused else "stopped") + ".")
        if not paused:
            self.__lastTimestamp__ = None
            self.__lastValue__ = None
            if reset:
                self.reset()

    def pause(self):
        self.stop(paused=True)
            
    def threadIsRunning(self):
        return self.__timer__ != None

    def threadIsInUse(self):
        return self.__timer__ != None or self.__lastTimestamp__ != None

    @property
    def messageCount(self):
        return self.__messageCounter__
    
    def info(self,msg):
        self.device.info(msg)
