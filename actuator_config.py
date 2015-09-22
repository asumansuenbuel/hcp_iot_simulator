# Actuator Configuration
# 
# Author: Asuman Suenbuel
# (c) 2015
#
# This file contains the pre-defined actuators for the simulator and
# the corresponding python function on how to create an instance of
# each of them.

from actuator import *


actuatorConstructors = {
    "LCD Display" : lambda : LcdDisplay(),
    "Red Led" : lambda : Led(color="red"),
    "Blue Led" : lambda : Led(color="blue"),
    "Green Led" : lambda : Led(color="green"),
    "Yellow Led" : lambda : Led(color="yellow"),
    "Simulation Controller" : lambda : SimulationController()
}

actuatorNames = actuatorConstructors.keys()

