# dbus-fronius-smartmeter Service

### Purpose

This service is meant to be run with Venus OS from Victron; e.g. on a Cerbo GX.

The Python script cyclically reads data from the Fronius SmartMeter via the Fronius REST API and publishes information on the dbus, using the service name com.victronenergy.grid. This makes the Venus OS work as if you had a physical Victron Grid Meter installed.

### Configuration

In the config.ini file, you should put the IP of your Fronius device that hosts the REST API. In my setup, it is the IP of the Fronius Symo, which gets the data from the Fronius Smart Metervia the RS485 connection between them.

### Installation

1. Create a subfolder under /data named dbus-fronius-smartmeter on your venus.
2. Copy all files and the service folder to the /data/dbus-fronius-smartmeter folder.
3. Set permissions for the install.sh file: `chmod a+x /data/dbus-fronius-smartmeter/install.sh`
4. The daemon-tools should automatically start this service within seconds.

### Debugging

When you think that the script crashes, start it directly from the command line:

`python /data/dbus-fronius-smartmeter/dbus-fronius-smartmeter.py`

and see if it throws any error messages.

If the script stops with the message `dbus.exceptions.NameExistsException: Bus name already exists: com.victronenergy.grid` it means that the service is still running or another service is using that bus name.

#### Restart the script

If you want to restart the script, for example after changing it, just run the following command:

`/data/dbus-fronius-smartmeter/restart.sh`

The daemon-tools will restart the script within a few seconds.

### Hardware

In my installation at home, I am using the following Hardware:
- Fronius Symo 17.5 - PV Grid Tied Inverter (three phases)
- Fronius Smart Meter 63A-3 - (three phases)
- 3 Victron MultiPlus-II - Battery Inverter (three phases)
- Victron Cerbo GX running Venus OS
- LiFePO Battery (16x EVE 280Ah)
- 123\SmartBMS
