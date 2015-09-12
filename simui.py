#
# main control window for simulator ui
#
import sys, os

from simulator_ui import *

sim = SimulatorUI()
if len(sys.argv) > 1:
    arg = sys.argv[1]
    if os.path.exists(arg):
        sim.load_file_on_init = arg

#import code
#code.interact(local=locals())

sim.openUI()

        
