#!/usr/bin/env python

import platform
import logging
import sys
import os
import time
import requests                                   # for http GET
import configparser                               # for config/ini file

try:    import gobject                            # Python 2.x
except: from gi.repository import GLib as gobject # Python 3.x
try:    import thread                             # for daemon = True / Python 2.x
except: import _thread as thread                  # for daemon = True / Python 3.x

sys.path.insert(1, os.path.join(os.path.dirname(__file__), '/opt/victronenergy/dbus-systemcalc-py/ext/velib_python'))
from vedbus import VeDbusService


class DbusFroniusSmartmeterService:
  def __init__(self, servicename, paths, productname='Fronius Smart Meter', connection='Fronius Smart Meter service'):

    self._dbusservice = VeDbusService(servicename)
    self._paths = paths

    logging.debug("%s /DeviceInstance = %d" % (servicename, 0))

    # Create the management objects, as specified in the ccgx dbus-api document
    self._dbusservice.add_path('/Mgmt/ProcessName', __file__)
    self._dbusservice.add_path('/Mgmt/ProcessVersion', 'Unknown version, and running on Python ' + platform.python_version())
    self._dbusservice.add_path('/Mgmt/Connection', connection)

    # Create the mandatory objects
    self._dbusservice.add_path('/DeviceInstance', 0)
    self._dbusservice.add_path('/ProductId', 16) # value used in ac_sensor_bridge.cpp of dbus-cgwacs
    self._dbusservice.add_path('/ProductName', productname)
    self._dbusservice.add_path('/CustomName', self._getConfig()['DEFAULT']['CustomName'])    
    self._dbusservice.add_path('/Connected', 1)
    self._dbusservice.add_path('/FirmwareVersion', 0.1)
    self._dbusservice.add_path('/HardwareVersion', 0)
    self._dbusservice.add_path('/UpdateIndex', 0)

    for path, settings in self._paths.items():
      self._dbusservice.add_path(path, settings['initial'], gettextcallback=settings['textformat'], writeable=True, onchangecallback=self._handlechangedvalue)

    gobject.timeout_add(250, self._update) # pause 250ms before the next request

  def _getConfig(self):
    config = configparser.ConfigParser()
    config.read("%s/config.ini" % (os.path.dirname(os.path.realpath(__file__))))
    return config;

  def _update(self):
    try:
      meter_url         = "http://%s/cm?cmnd=status%208" % (self._getConfig()['DEFAULT']['Host'])
      meter_r           = requests.get(url=meter_url) # request data from the Fronius PV inverter
      meter_data        = meter_r.json() # convert JSON data

      meter_model       =  'GS303'
      meter_consumption = float(meter_data['StatusSNS']['GS303']['Power_cur'])
      energy_consumed = float(meter_data['StatusSNS']['GS303']['Total_in'])
      energy_delivered = float(meter_data['StatusSNS']['GS303']['Total_out'])

      # set values because they are not available :-( hopefully they are not necessary - if, they should be calculated)
      meter_data['Body']['Data']['Voltage_AC_Phase_1']  = 0
      meter_data['Body']['Data']['Voltage_AC_Phase_2']  = 0
      meter_data['Body']['Data']['Voltage_AC_Phase_3']  = 0
      meter_data['Body']['Data']['Current_AC_Phase_1']  = 0
      meter_data['Body']['Data']['Current_AC_Phase_2']  = 0
      meter_data['Body']['Data']['Current_AC_Phase_3']  = 0
      meter_data['Body']['Data']['PowerReal_P_Phase_1'] = 0
      meter_data['Body']['Data']['PowerReal_P_Phase_2'] = 0
      meter_data['Body']['Data']['PowerReal_P_Phase_3'] = 0

      meter_data['Body']['Data']['EnergyReal_WAC_Sum_Consumed'] = energy_consumed
      meter_data['Body']['Data']['EnergyReal_WAC_Sum_Produced'] = energy_delivered

      self._dbusservice['/Ac/Power']          = meter_consumption # positive: consumption, negative: feed into grid
      self._dbusservice['/Ac/L1/Voltage']     = meter_data['Body']['Data']['Voltage_AC_Phase_1']
      self._dbusservice['/Ac/L2/Voltage']     = meter_data['Body']['Data']['Voltage_AC_Phase_2']
      self._dbusservice['/Ac/L3/Voltage']     = meter_data['Body']['Data']['Voltage_AC_Phase_3']
      self._dbusservice['/Ac/L1/Current']     = meter_data['Body']['Data']['Current_AC_Phase_1']
      self._dbusservice['/Ac/L2/Current']     = meter_data['Body']['Data']['Current_AC_Phase_2']
      self._dbusservice['/Ac/L3/Current']     = meter_data['Body']['Data']['Current_AC_Phase_3']
      self._dbusservice['/Ac/L1/Power']       = meter_data['Body']['Data']['PowerReal_P_Phase_1']
      self._dbusservice['/Ac/L2/Power']       = meter_data['Body']['Data']['PowerReal_P_Phase_2']
      self._dbusservice['/Ac/L3/Power']       = meter_data['Body']['Data']['PowerReal_P_Phase_3']
      self._dbusservice['/Ac/Energy/Forward'] = float(meter_data['Body']['Data']['EnergyReal_WAC_Sum_Consumed']) # energy bought from the grid
      self._dbusservice['/Ac/Energy/Reverse'] = float(meter_data['Body']['Data']['EnergyReal_WAC_Sum_Produced']) # energy sold to the grid

      logging.debug("Consumption: {:.0f}W".format(meter_consumption))

      # increment UpdateIndex - to show that new data is available
      index = self._dbusservice['/UpdateIndex'] + 1
      if index > 255: index = 0
      self._dbusservice['/UpdateIndex'] = index

    except Exception as e:
      logging.critical('Error at %s', '_update', exc_info=e)
      self._dbusservice['/Ac/Power'] = 0

    return True

  def _handlechangedvalue(self, path, value):
    logging.debug("someone else updated %s to %s" % (path, value))
    return True # accept the change

def main():
  logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
      logging.FileHandler("%s/current.log" % (os.path.dirname(os.path.realpath(__file__)))),
      logging.StreamHandler()
    ]
  )
  thread.daemon = True # allow the program to quit

  from dbus.mainloop.glib import DBusGMainLoop # have a mainloop, so we can send/receive asynchronous calls to and from dbus
  DBusGMainLoop(set_as_default=True)

  #formatting 
  _kwh = lambda p, v: "{:.0f}kWh".format(v)
  _w   = lambda p, v: "{:.0f}W".format(v)
  _a   = lambda p, v: "{:.1f}A".format(v)
  _v   = lambda p, v: "{:.1f}V".format(v)
 
  pvac_output = DbusGS303SmartmeterService(
    servicename='com.victronenergy.grid',
    paths={
      '/Ac/Power':             {'initial': 0, 'textformat': _w},

      '/Ac/L1/Voltage':        {'initial': 0, 'textformat': _v},
      '/Ac/L2/Voltage':        {'initial': 0, 'textformat': _v},
      '/Ac/L3/Voltage':        {'initial': 0, 'textformat': _v},

      '/Ac/L1/Current':        {'initial': 0, 'textformat': _a},
      '/Ac/L2/Current':        {'initial': 0, 'textformat': _a},
      '/Ac/L3/Current':        {'initial': 0, 'textformat': _a},

      '/Ac/L1/Power':          {'initial': 0, 'textformat': _w},
      '/Ac/L2/Power':          {'initial': 0, 'textformat': _w},
      '/Ac/L3/Power':          {'initial': 0, 'textformat': _w},

      '/Ac/Energy/Forward':    {'initial': 0, 'textformat': _kwh}, # energy bought from the grid
      '/Ac/Energy/Reverse':    {'initial': 0, 'textformat': _kwh}, # energy sold to the grid
    }
  )

  logging.debug('Connected to dbus, and switching over to gobject.MainLoop() (= event based)')
  mainloop = gobject.MainLoop()
  mainloop.run()

if __name__ == "__main__": main()
