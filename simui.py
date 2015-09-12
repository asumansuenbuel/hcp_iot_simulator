#
# main control window for simulator ui
#
import sys, os

from simulator_ui import *
from process_argv import *
from sim_utils import defaultDataFolder

sim = SimulatorUI()

cmdLine = CommandLine()
if cmdLine.parse():
    if hasattr(cmdLine,'fileArgument'):
        sim.load_file_on_init = cmdLine.fileArgument

    ensureDataFolderExists()
    sim.openUI()


        
