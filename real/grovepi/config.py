#
#
# configuration of RaspberryPi with GrovePi sensor board
#

from sim_utils import runs_on_raspberry

try:
    from grovepi import *
    from grove_rgb_lcd import *
except:
    pass

id = "grovepi"
name = "RaspberryPi with GrovePi"
uuid = "MAC_ADDRESS"

actuatorIds = ['lcdDisplay','greenLed']

sensorIds = ['temperature','humidity','light','ranger']

# --------------------------------------------------------------------------------
# Actuators
# --------------------------------------------------------------------------------

def greenLed_init(device):
    led = 4
    device.greenLedPin = led
    pinMode(led,"OUTPUT")

def greenLed_processMessage(device,message):
    led = device.greenLedPin
    onoff = message['operand']
    if onoff == "on":
        digitalWrite(led,1)
    else:
        digitalWrite(led,0)

def lcdDisplay_init(device):
    print 'initializing real lcdDisplay...'

def lcdDisplay_processMessage(device,message):
    text = message['operand']
    print "setting text in read lcdDisplay \"" + text + "\""
    try:
        setText(text)
    except Exception as e:
        print "[" + str(e) + "]"

# --------------------------------------------------------------------------------
# Sensors
# --------------------------------------------------------------------------------

def temperature_init(sensor):
    sensor.name = "Temperature"
    sensor.unitName = "C"
    sensor.dht_sensor_port = 7
    print "temperature sensor initialized."

def temperature_getValue(sensor):
    [ temp,hum ] = dht(sensor.dht_sensor_port,0)
    #setText("temperature: " + str(temp) + "C")
    return temp

def humidity_init(sensor):
    sensor.name = "Humidity"
    sensor.unitName = "%"
    sensor.dht_sensor_port = 7
    print "humidity sensor initialized."

def humidity_getValue(sensor):
    [ temp,hum ] = dht(sensor.dht_sensor_port,0)
    return hum
    
def light_init(sensor):
    sensor.name = "Light"
    sensor.unitName = "Lux"
    sensor.lightInput = 1

def light_getValue(sensor):
    return analogRead(sensor.lightInput)


def ranger_init(sensor):
    sensor.name = "UltrasonicRanger"
    sensor.unitName = "cm"
    sensor.rangerInput = 3

def ranger_getValue(sensor):
    pin = sensor.rangerInput
    return ultrasonicRead(pin)
