# class representing a real sensor device
#
# 
# Author: Asuman Suenbuel
# (c) 2015
#

from sim_utils import *
import actuator_config
from sensor import *

class RealDevice(FilePersistedObject):

    def __init__(self,id=None,config=None):
        print "creating real device object..."
        if id != None and config != None:
            raise Exception("you cannont specify both 'id' and 'config' to create a 'RealDevice' object.")
        if id == None and config == None:
            raise Exception("you have to specify either 'id' or 'config' to create a 'RealDevice' object.")
        
        self.__init_from_config__(config)
        self.__init_from_id__(id)

        self.__device__ = None

    # --------------------------------------------------------------------------------
    def __init_from_config__(self,config):
        if config == None:
            return
        if config.uuid == "MAC_ADDRESS":
            try:
                self.uuid = open('/sys/class/net/eth0/address').read().strip()
            except:
                self.uuid = config.uuid
        else:
            self.uuid = config.uuid
                
        self.name = config.name

        self.actuatorHooks = {}
        # initialize real actuators
        for aid in actuator_config.actuatorIds:
            #print 'actuator id: "' + aid + '"'
            obj = {}
            addObj = False
            for suffix in ['init','processMessage']:
                funName = aid + '_' + suffix
                if hasattr(config,funName):
                    print funName + ' found'
                    obj[suffix] = getattr(config,funName)
                    addObj = True
            if addObj:
                self.actuatorHooks[aid] = obj
                print 'actuator hook for "' + aid + '" added.'
        # initialize real sensors
        self.sensorHooks = {}
        if hasattr(config,'sensorIds'):
            sensorIds = config.sensorIds
            #print "found real sensor ids: " + str(sensorIds)
            for sid in sensorIds:
                obj = {}
                addObj = False
                for suffix in ['init','getValue','getInfo']:
                    funName = sid + '_' + suffix
                    if hasattr(config,funName):
                        print funName + ' found'
                        obj[suffix] = getattr(config,funName)
                        addObj = True
                if addObj:
                    self.sensorHooks[sid] = obj
                    print 'sensor hook for "' + sid + '" added.'

    # --------------------------------------------------------------------------------
    def __init_from_id__(self,id):
        if id == None:
            return
        mname = 'real.' + id + '.config'
        print "mname: " + mname
        exec 'import ' + mname + ' as realDeviceConfig'
        self.__init_from_config__(realDeviceConfig)

    # --------------------------------------------------------------------------------

    @property
    def device(self):
        return self.__device__

    @device.setter
    def device(self,d):
        self.__device__ = d
        d.name = self.name
        d.uuid = self.uuid
        d.realDevice = self
        for actuatorId in self.actuatorHooks.keys():
            print 'adding actuator "' + actuatorId + '" to device...'
            d.addActuatorId(actuatorId)

        for sensorId in self.sensorHooks.keys():
            obj = self.sensorHooks[sensorId]
            print 'adding sensor "' + sensorId + '" to device...'
            initialName = sensorId
            sensor = d.createSensor(name=initialName,isRealSensor=True)
            if obj.has_key('getValue'):
                sensor.getRealValue = obj['getValue']
            if obj.has_key('getInfo'):
                sensor.getRealInfo = obj['getInfo']
            try:
                fun = obj['init']
                fun(sensor)
                print sensor
            except:
                pass
            d.addSensor(sensor)
            
            
