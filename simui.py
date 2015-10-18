#
# main control window for simulator ui
#
# 
# Author: Asuman Suenbuel
# (c) 2015
#

import sys, os


from simulator_ui import *
from process_argv import *
from sim_utils import defaultDataFolder

sim = SimulatorUI()

#print "current working directory: " + os.getcwd()

cmdLine = CommandLine()
realDeviceId = None
if os.environ.has_key('SIMULATOR_DEVICE_ID'):
    realDeviceId = os.environ['SIMULATOR_DEVICE_ID']
    
if cmdLine.parse():
    if hasattr(cmdLine,'fileArgument'):
        sim.load_file_on_init = cmdLine.fileArgument

    elif cmdLine.hasoption('device'):
        realDeviceId = cmdLine.getoption('device')

    if cmdLine.hasoption('pollingInterval'):
        sim.pollingInterval = cmdLine.getoption('pollingInterval')

        
    ensureDataFolderExists()
    if realDeviceId != None:
        sim.realDeviceId = realDeviceId
    
    sim.openUI()
