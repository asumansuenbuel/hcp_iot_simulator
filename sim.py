# main command line for hcp iot simulator
#
# 
# Author: Asuman Suenbuel
# (c) 2015
#

import code
import readline
import atexit
from device import *
from simulator import *
from process_argv import *

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
                 histfile=os.path.expanduser("~/.console-history")):
        code.InteractiveConsole.__init__(self, locals, filename)
        self.init_history(histfile)

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

sim = Simulator()
msg = 'Simulator instance stored in Python variable "sim".\n'
cmdLine = CommandLine()
if cmdLine.parse():
    if hasattr(cmdLine,'fileArgument'):
        try:
            sim.loadFromFile(cmdLine.fileArgument)
            msg += '\nFile "' + cmdLine.fileArgument + '" loaded successfully.\n'
        except Exception as e:
            msg += '\n*** Cannot initialize simulator from file "' + cmdLine.fileArgument + '": ' + str(e) + '\n'

    ensureDataFolderExists()

print '\n' + msg + '\n'
HCPSimulatorConsole(locals=locals()).interact()
