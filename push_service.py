# Push to HCP service class
# 
# Author: Asuman Suenbuel
# (c) 2015
#

import time, threading, random, json, sys, urllib3, os
from device import *
from sim_utils import *
import actuator_config

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


# ================================================================================
#
# PushService class
#
# ================================================================================


# The PushService class can be used to push messages to HCP. It can be
# initialized with or without a device object. If a device object is
# specified, it's HCP parameters are used to create the push message:
# the hcpDeviceId and the messageTypeIdToDevice
#
class PushService:

    def __init__(self,simulator=None,device=None,actuator=None,method="http",name="PushService",hcpDeviceId=None,messageTypeIdToDevice=None,messageFields=actuator_config.messageFields):
        self.simulator = simulator
        self.device = device
        self.actuator = actuator
        self.method = method
        self.name = name
        self._hcpDeviceId = hcpDeviceId
        self._messageTypeIdToDevice = messageTypeIdToDevice
        self.messageFields = messageFields
        self.messageFieldNames = map(lambda obj : obj['name'], messageFields)


    @property
    def hcpDeviceId(self):
        if self._hcpDeviceId != None:
            return self._hcpDeviceId
        if self.device != None:
            return self.device.hcpDeviceId
        return config.hcp_device_id

    @hcpDeviceId.setter
    def hcpDeviceId(self,value):
        self._hcpDeviceId = value
    
    @property
    def messageTypeIdToDevice(self):
        if self._messageTypeIdToDevice != None:
            return self._messageTypeIdToDevice
        if self.device != None:
            return self.device.messageTypeIdToDevice
        return config.hcp_message_type_id_to_device

    @messageTypeIdToDevice.setter
    def messageTypeIdToDevice(self,value):
        self._messageTypeIdToDevice = value


    # sets up the push operation using the following options (default values in square brackets):
    #
    # device [self.device] : gets the hcp ids from the device if given
    # hcpDeviceId [None] : specifies the hcp device id, this takes preference over device parameter
    # messageTypeIdToDevice [None] : specifies the hcp message type id, this takes preference over device parameter
    # actuator [self.actuator] : an instance of Actuator, if the messageFields use a default value with $actuator or $actuator_id, the
    #                   actuator's id is substituted in the payload if this field is not specified as a payload field (see below)
    # <any payload field> : the arguments can contain any name of the payload as specified in the messageFields list. The method
    #                       checks and completes the payload using defaultValues according to this list as well. An Exception is
    #                       raised if required fields are missing.
    def push(self,**options):
        device = self.device
        hcpDeviceId = None
        messageTypeIdToDevice = None
        payload = {}
        actuatorObject = self.actuator
        dummyMode = False
        for key,value in options.iteritems():
            print key + " -> " + str(value)
            if key == 'device':
                device = value
            elif key == 'hcpDeviceId':
                hcpDeviceId = value
            elif key == 'messageTypeIdToDevice':
                messageTypeIdToDevice = value
            elif key == 'actuator':
                if not isinstance(value,Actuator):
                    raise Exception('value of actuator argument is not an instance of class Actuator.')
                else:
                    actuatorObject = value
            elif key == 'dummyMode':
                dummyMode = value
            elif key in self.messageFieldNames:
                payload[key] = value
            else:
                raise Exception('unrecognized key,value pair in push-service: ("' + key + '","' + value + '")')

        self._checkAndCompletePayload(payload,device=device,actuator=actuatorObject)

        hcpDeviceId = hcpDeviceId if hcpDeviceId != None else (
            device.hcpDeviceId if device != None else self.hcpDeviceId)

        messageTypeIdToDevice = messageTypeIdToDevice if messageTypeIdToDevice != None else (
            device.messageTypeIdToDevice if device != None else self.messageTypeIdToDevice)

        if hcpDeviceId == None or messageTypeIdToDevice == None:
            raise Exception("cannot perform push operation: you forgot to specify hcpDeviceId and/or messageTypeIdToDevice.")
        
        self._doPushToHCP(hcpDeviceId,messageTypeIdToDevice,payload,dummyMode=dummyMode)

    def _checkAndCompletePayload(self,payload,device=None,actuator=None,doCheck=True):
        for field in self.messageFields:
            fname = field['name']
            if payload.has_key(fname):
                continue
            required = field['required'] if field.has_key('required') else False
            if required:
                if field.has_key('defaultValue'):
                    defaultValue = field['defaultValue']
                    if actuator != None or device != None:
                        tmpl = Template(defaultValue)
                        defaultValue = tmpl.safe_substitute(actuator_id=actuator.id,actuator=actuator.id,actuator_name=actuator.name)
                    payload[fname] = defaultValue
                else:
                    if doCheck:
                        raise Exception('payload is missing required field "' + fname + '"')
                    else:
                        payload[fname] = 'value required'
            else:
                payload[fname] = 'value optional'

    def completePayload(self,payload,actuator=None):
        if actuator == None:
            actuator = self.actuator
        self._checkAndCompletePayload(payload,actuator=actuator,doCheck=False)

    def createInitialPayload(self,actuator=None):
        payload = {}
        self.completePayload(payload,actuator=actuator)
        return payload

    # this method does the actual http-push to HCP using the parameters collecting in the push method
    def _doPushToHCP(self,hcpDeviceId,messageTypeIdToDevice,payload,dummyMode=False):
        try:
            urllib3.disable_warnings()
        except:
            print("urllib3.disable_warnings() failed - get a recent enough urllib3 version to avoid potential InsecureRequestWarning warnings! Will continue though.")

        # use with or without proxy
        if (config.proxy_url == ''):
            http = urllib3.PoolManager()
        else:
            http = urllib3.proxy_from_url(config.proxy_url)

        push_url='https://iotmms' + config.hcp_account_id + config.hcp_landscape_host + '/com.sap.iotservices.mms/v1/api/http/push/' + str(hcpDeviceId)
        self.info(push_url)
        # use with authentication
        headers = urllib3.util.make_headers(user_agent=None)
        headers['Authorization'] = config.hcp_authorization_header
        headers['Content-Type'] = 'application/json;charset=utf-8'

        bodyObj = {
            'method' : self.method,
            'sender' : self.name,
            'messageType' : messageTypeIdToDevice,
            'messages' : [payload]
        }
	body = json.dumps(bodyObj)
        self.info("pushing to hcp: " + body)
        if dummyMode:
            self.info("Dummy mode is active, not pushing anything to HCP.")
            return
        r = http.urlopen('POST', push_url, body=body, headers=headers)
        self.info('push_to_hcp(): ' + str(r.status) + ' ' + r.data)

    def info(self,msg):
        print msg
