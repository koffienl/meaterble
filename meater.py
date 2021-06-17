from bluepy import btle
import time
import ConfigParser
import os,sys

MQTT_SERVER = ""
MQTT_PORT = ""
MQTT_USERNAME = ""
MQTT_PASSWORD = ""
MQTT_TOPIC = ""
counter = 10

__all__ = ['MeaterProbe']

def ConfigSectionMap(Config, section):
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.get(section, option)
            if dict1[option] == -1:
                print("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1
 
class MeaterProbe:
   def __init__(self, addr):
      #self._addr = addr
      #self.connect()
      #self.update()

      global MQTT_SERVER
      global MQTT_PORT
      global MQTT_USERNAME
      global MQTT_PASSWORD
      global MQTT_TOPIC

      pathname = os.path.dirname(sys.argv[0])
      Config = ConfigParser.ConfigParser()
      Config.read(os.path.abspath(pathname)+"/meater.ini")

      MQTT_SERVER = ConfigSectionMap(Config, "MQTT")['server']
      MQTT_PORT = ConfigSectionMap(Config, "MQTT")['port']
      MQTT_USERNAME = ConfigSectionMap(Config, "MQTT")['username']
      MQTT_PASSWORD = ConfigSectionMap(Config, "MQTT")['password']
      MQTT_TOPIC = ConfigSectionMap(Config, "MQTT")['topic']

      #print "mqtt server: "
      #print MQTT_SERVER

      self._addr = addr
      self.connect()
      self.update()

       
   @staticmethod
   def bytesToInt(byte0, byte1):
      return byte1*256+byte0

   @staticmethod
   def convertAmbient(array): 
      tip = MeaterProbe.bytesToInt(array[0], array[1])
      ra  = MeaterProbe.bytesToInt(array[2], array[3])
      oa  = MeaterProbe.bytesToInt(array[4], array[5])
      return int(tip+(max(0,((((ra-min(48,oa))*16)*589))/1487)))
      
   @staticmethod
   def toCelsius(value):
      return (float(value)+8.0)/16.0

   @staticmethod
   def toFahrenheit(value):
      return ((MeaterProbe.toCelsius(value)*9)/5)+32.0

   def getTip(self):
      return self._tip

   def getTipF(self):
      return MeaterProbe.toFahrenheit(self._tip)

   def getTipC(self):
      return MeaterProbe.toCelsius(self._tip)

   def getAmbientF(self):
      return MeaterProbe.toFahrenheit(self._ambient)

   def getAmbient(self):
      return self._ambient

   def getAmbientC(self):
      return MeaterProbe.toCelsius(self._ambient)

   def getBattery(self):
      return self._battery

   def getAddress(self):
      return self._addr

   def getID(self):
      return self._id

   def getFirmware(self):
      return self._firmware

   def connect(self):
      self._dev = btle.Peripheral(self._addr)

   def readCharacteristic(self, c):
      return bytearray(self._dev.readCharacteristic(c))

   def update(self):
      import paho.mqtt.client as mqtt
      global counter
      global MQTT_SERVER
      global MQTT_PORT
      global MQTT_USERNAME
      global MQTT_PASSWORD
      global MQTT_TOPIC

      model = str(self.readCharacteristic(3))
      if model == 'MEATER':
         tempBytes = self.readCharacteristic(31)
         batteryBytes = self.readCharacteristic(35)

      if model == 'MEATER+':
         tempBytes = self.readCharacteristic(36)
         batteryBytes = self.readCharacteristic(40)

      self._tip = MeaterProbe.bytesToInt(tempBytes[0], tempBytes[1])
      self._ambient = MeaterProbe.convertAmbient(tempBytes)
      self._battery = MeaterProbe.bytesToInt(batteryBytes[0], batteryBytes[1])*10
      self._lastUpdate = time.time()

      if counter >= 10:
         print "send mqtt"
         client = mqtt.Client()
         client.username_pw_set(MQTT_USERNAME, password=MQTT_PASSWORD)
         client.connect(MQTT_SERVER, MQTT_PORT)
         client.loop_start()

         client.publish(MQTT_TOPIC + "/last_updated", self._lastUpdate)
         client.publish(MQTT_TOPIC + "/mac", self.getAddress())
         client.publish(MQTT_TOPIC + "/battery", self.getBattery())
         client.publish(MQTT_TOPIC + "/tip", round(self.getTipC(),0))
         client.publish(MQTT_TOPIC + "/ambient", round(self.getAmbientC(),0))
         client.publish(MQTT_TOPIC + "/model", model)

         counter = 0

      counter = counter + 1

   def __str__(self):
       #return "%s %s probe: %s tip: %fF/%fC ambient: %fF/%fC battery: %d%% age: %ds" % (self.getAddress(), self.getFirmware(), self.getID(), self.getTipF(), self.getTipC(), self.getAmbientF(), self.getAmbientC(), self.getBattery(), time.time() - self._lastUpdate)
       return "%s probe: tip: %fF/%fC ambient: %fF/%fC battery: %d%% age: %ds" % (self.getAddress(), self.getTipF(), self.getTipC(), self.getAmbientF(), self.getAmbientC(), self.getBattery(), time.time() - self._lastUpdate)

