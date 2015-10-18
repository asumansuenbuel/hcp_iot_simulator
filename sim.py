# main command line for hcp iot simulator
#
# 
# Author: Asuman Suenbuel
# (c) 2015
#

import code
import sys
import readline
import atexit
from device import *
from simulator import *
from process_argv import *

from webserver import *

try:
    import readline
except ImportError:
    print "Module readline not available."
else:
    import rlcompleter
    readline.parse_and_bind("tab: complete")

# shell commands
print "\nStarting HCP Simulator Python shell; history and completion enabled..."
#code.interact(local=locals())

def help():
    print '''

'''

# initialize a default Simulator using the variable name "sim"

sim = Simulator()

class HCPSimulatorConsole(code.InteractiveConsole):
    def __init__(self, locals=None, filename="<console>",
                 histfile=os.path.expanduser("~/.console-history"),simulator=None):
        code.InteractiveConsole.__init__(self, locals, filename)
        self.init_history(histfile)
        self.simulator = simulator

    def init_history(self, histfile):
        if 'libedit' in readline.__doc__:
            readline.parse_and_bind("bind ^I rl_complete")
        else:
            readline.parse_and_bind("tab: complete")
        if hasattr(readline, "read_history_file"):
            try:
                readline.read_history_file(histfile)
            except IOError:
                pass
            atexit.register(self.save_history, histfile)

    def save_history(self, histfile):
        readline.write_history_file(histfile)

    def cleanup(self):
        sim = self.simulator
        if sim == None:
            return
        self.write('cleaning up...\n')
        sim.cleanupOnExit()

    def interact(self,banner = None):
        try:
            sys.ps1
        except AttributeError:
            sys.ps1 = ">>> "
        try:
            sys.ps2
        except AttributeError:
            sys.ps2 = "... "

        if banner != None:
            self.write("%s\n" % str(banner))

        more = 0
        while 1:
            try:
                if more:
                    prompt = sys.ps2
                else:
                    prompt = sys.ps1
                try:
                    line = self.raw_input(prompt)
                except EOFError:
                    self.write("\n")
                    self.cleanup()
                    break
                else:
                    more = self.push(line)
            except KeyboardInterrupt:
                self.write("KeyboardInterrupt\n")
                self.cleanup()
                self.resetbuffer()
                break
                more = 0

sim = Simulator()
msg = 'Simulator instance stored in Python variable "sim".\n'
cmdLine = CommandLine()

realDeviceId = None
if os.environ.has_key('SIMULATOR_DEVICE_ID'):
    realDeviceId = os.environ['SIMULATOR_DEVICE_ID']

if cmdLine.parse():
    if hasattr(cmdLine,'fileArgument'):
        try:
            sim.loadFromFile(cmdLine.fileArgument)
            msg += '\nFile "' + cmdLine.fileArgument + '" loaded successfully.\n'
        except Exception as e:
            msg += '\n*** Cannot initialize simulator from file "' + cmdLine.fileArgument + '": ' + str(e) + '\n'

    elif cmdLine.hasoption('device'):
        realDeviceId = cmdLine.getoption('device')

    if cmdLine.hasoption('pollingInterval'):
        sim.pollingInterval = cmdLine.getoption('pollingInterval')

    if cmdLine.hasoption('noPolling'):
        sim.noPolling = True    
            
    ensureDataFolderExists()

if realDeviceId != None:
    sim.realDeviceId = realDeviceId

print '\n' + msg + '\n'
if len(sim.devices) > 0:
    for i in range(len(sim.devices)):
        estr = 'd' + str(i) + ' = sim.devices[' + str(i) + ']'
        exec estr in globals(),locals()

sim.postInit()

if cmdLine.hasoption('startWebserver') and cmdLine.getoption('startWebserver'):
    ws = Webserver(simulator=sim,port=cmdLine.getoption('webserverPort'))
    ws.start()
else:
    try:
        HCPSimulatorConsole(locals=locals(),simulator=sim).interact()
    except KeyboardInterrupt:
        print "keyboard interrupt"
