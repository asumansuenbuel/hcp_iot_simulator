#
# main command line window for simulator
#
import code
from device import *
from simulator import *
try:
    import readline
except ImportError:
    print "Module readline not available."
else:
    import rlcompleter
    readline.parse_and_bind("tab: complete")

# shell commands
print "\nHCP Simulator\n"
code.interact(local=locals())
