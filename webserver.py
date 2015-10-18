# Web server interface to simulator
#
# 
# Author: Asuman Suenbuel
# (c) 2015
#

'''
The web server interface provides an interface into the simulator by means of Http requests.
This is particularly useful for connecting remote devices to a running simulator instance.
'''

import BaseHTTPServer
import time
import json
import re

PORT = 6540

class Webserver(BaseHTTPServer.HTTPServer):


    def __init__(self,*args,**kwargs):
        kwargs0 = dict(kwargs)
        del kwargs0['port']
        del kwargs0['simulator']
        self.port = PORT
        if ('port' in kwargs) and (kwargs['port'] != None):
            self.port = kwargs['port']

        BaseHTTPServer.HTTPServer.__init__(self,('',self.port),SimRequestHandler)

        if 'simulator' in kwargs:
            self.simulator = kwargs['simulator']
        else:
            raise Exception('Webserver must be given a "simulator" instance on initialization')


    def start(self,*args,**kwargs):
        print "starting webserver on port " + str(self.port) + "..."
        try:
            self.serve_forever()
        except KeyboardInterrupt:
            pass
        self.server_close()


class SimRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    @property
    def simulator(self):
        return self.server.simulator
    
    def OK(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        return self

    def ERROR(self,errmsg):
        self.send_response(400)
        self.send_header("Content-type", "application/json")
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        obj = {'error' : str(errmsg)}
        self.write(obj);

    def write(self,t):
        self.wfile.write(t)
        return self

    def json(self,obj):
        self.write(json.dumps(obj))
    
    def do_GET(self):
        try:
            devicePathPattern = re.compile('^/device/([0-9]+)$')
            devicePathPatternMatch = devicePathPattern.match(self.path)
            deviceInfoPattern = re.compile('^/device/([0-9]+)/info$')
            deviceInfoPatternMatch = deviceInfoPattern.match(self.path)
            deviceSensorValuesPattern = re.compile('^/device/([0-9]+)/sensorvalues$')
            deviceSensorValuesPatternMatch = deviceSensorValuesPattern.match(self.path)
            devicePollingIsRunningPattern = re.compile('^/device/([0-9]+)/pollingisrunning$')
            devicePollingIsRunningPatternMatch = devicePollingIsRunningPattern.match(self.path)
            if (self.path == '/info') or (self.path == '/'):
                obj = self.simulator.toJson()
                self.OK().json(obj)
            elif self.path == '/devices':
                obj = self.simulator.toJson()['devices']
                self.OK().json(obj)
            elif devicePathPatternMatch:
                indexstr = devicePathPatternMatch.group(1)
                index = int(indexstr)
                obj = self.simulator.toJson()['devices'][index]
                self.OK().json(obj)
            elif deviceInfoPatternMatch:
                indexstr = deviceInfoPatternMatch.group(1)
                index = int(indexstr)
                d = self.simulator.devices[index]
                obj = {
                    'messages' : d.infoBuffer,
                    'payload' : d.payloadBuffer,
                    'threadsAreRunning' : d.threadsAreRunning(),
                    'pollingisrunning' : d.pollingIsRunning
                }
                self.OK().json(obj)
            elif deviceSensorValuesPatternMatch:
                indexstr = deviceSensorValuesPatternMatch.group(1)
                index = int(indexstr)
                d = self.simulator.devices[index]
                obj = d._collectSensorValues()
                self.OK().json(obj)
            elif devicePollingIsRunningPatternMatch:
                indexstr = devicePollingIsRunningPatternMatch.group(1)
                index = int(indexstr)
                d = self.simulator.devices[index]
                obj = {'result' : d.pollingIsRunning}
                self.OK().json(obj)
            else:
                self.ERROR("invalid http request: " + str(self.path))
        except Exception as e:
            self.ERROR(str(e))


    def do_POST(self):
        print "POST: path=" + str(self.path)
        devicePattern = re.compile('^/device/([0-9]+)$')
        devicePatternMatch = devicePattern.match(self.path)
        msg = "no message"
        try:
            if devicePatternMatch:
                obj = {'result':'success'}
                contentLength = int(self.headers.getheader('Content-Length'))
                data = self.rfile.read(contentLength)
                print "data: " + str(data)
                jsonData = json.loads(data)
                indexstr = devicePatternMatch.group(1)
                index = int(indexstr)
                d = self.simulator.devices[index]
                msg = "processing remote command failed"
                res = d._processRemoteCommand(jsonData)
                msg = "processing remote command ok"
                if res != None:
                    obj = res
                self.OK().json(obj)
            else:
                self.ERROR("invalid http request: " + str(self.path))                
        except Exception as e:
            errmsg = str(e) + " [" + msg + "]"
            print errmsg
            self.ERROR(errmsg)
