# dbus-gs303-smartmeter Service

### Purpose

This service is meant to be run with Venus OS from Victron; e.g. on a Cerbo GX.

The Python script cyclically reads data from the GS303 SmartMeter via Tasmota JSON and publishes information on the dbus, using the service name com.victronenergy.grid. This makes the Venus OS work as if you had a physical Victron Grid Meter installed. Since the GS303 gives only the sum of power and not the power, voltage and current for each phase, these are calculated.

### Configuration

In the `config.ini` file, you should put the IP of your Tasmota device that reads the GS303.

### Installation

1. Create a subfolder under `/data` named `dbus-gs303-smartmeter` on your venus.
2. Copy all files and the service folder to the `/data/dbus-gs303-smartmeter` folder.
3. Set permissions for the install.sh file: `chmod a+x /data/dbus-gs303-smartmeter/install.sh`
4. The daemon-tools should automatically start this service within seconds.

### Debugging

When you think that the script crashes, start it directly from the command line:

`python /data/dbus-gs303-smartmeter/dbus-fronius-smartmeter.py`

and see if it throws any error messages.

If the script stops with the message `dbus.exceptions.NameExistsException: Bus name already exists: com.victronenergy.grid` it means that the service is still running or another service is using that bus name.

#### Restart the script

If you want to restart the script, for example after changing it, just run the following command:

`/data/dbus-gs303-smartmeter/restart.sh`

The daemon-tools will restart the script within a few seconds.

### Hardware

In my installation at home, I am using the following Hardware:
- Fronius Symo - PV Grid Tied Inverter (three phases)
- GS303 Smartmeter - (three phases)
- ESP32 with Tasmota Firmware with SML Decoder an IR Transistor Receiver 
- Victron MultiPlus - Battery Inverter (single phases)
- RPI running Venus OS
- Battery
