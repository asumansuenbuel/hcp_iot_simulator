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
            opts, args = getopt.getopt(self.argv,"wp:i:hd:x:",["dataFolder=","device=","polling-interval=","port=","no-polling"])
        except getopt.GetoptError as e:
            print str(e)
            return False
        
        for opt,arg in opts:
            if opt in ("-d","--dataFolder"):
                self.options['defaultDataFolder'] = arg
            elif opt in ("--device"):
                self.options['device'] = arg
            elif opt in ("-i","--polling-interval"):
                try:
                    num = float(arg)
                    self.options['pollingInterval'] = num
                except ValueError:
                    raise Exception("argument to '" + opt + "' must be a number")
            elif opt in ("-p","--port","-w"):
                self.options['startWebserver'] = True
                if arg != '':
                    try:
                        port = int(arg)
                        self.options['webserverPort'] = port
                    except ValueError:
                        raise Exception("argument to '" + opt + "' (the webserver port number) must be an integer number")
                else:
                    self.options['webserverPort'] = None
            elif opt in ("--no-polling"):
                self.options['noPolling'] = True

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
