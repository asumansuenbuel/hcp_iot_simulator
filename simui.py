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
if cmdLine.parse():
    if hasattr(cmdLine,'fileArgument'):
        sim.load_file_on_init = cmdLine.fileArgument

    ensureDataFolderExists()
    sim.openUI()


        
