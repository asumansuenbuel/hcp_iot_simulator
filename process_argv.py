#
# process the command line arguments of the simulator
#
# 
# Author: Asuman Suenbuel
# (c) 2015
#


import getopt, os, sys

class CommandLine:

    def __init__(self,argv=sys.argv[1:]):
        self.argv = argv
        self.options = {}

    def parse(self):
        try:
            opts, args = getopt.getopt(self.argv,"hd:",["dataFolder="])
        except getopt.GetoptError as e:
            print str(e)
            return False
        
        for opt,arg in opts:
            if opt in ("-d","--dataFolder"):
                self.options['defaultDataFolder'] = arg

        self.args = args
        if len(args) > 1:
            print "too many command line arguments: " + str(args[1:])
            return False

        if len(args) > 0:
            arg = args[0]
            if os.path.exists(arg):
                self.fileArgument = arg
            else:
                print 'File "' + arg + '" does not exist.'
                return False

        return True

    def hasoption(self,option):
        return option in self.options

    def getoption(self,option):
        return self.options[option]
