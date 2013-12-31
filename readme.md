Vestigo - Bluetooth tracking system
========================================================

What is it
------------
Vestigo is a proof of concept and educational project I took on to learn about, develop and show the ability and practicality of using the Bluetooth standard as a means to track asset locations in real-time.

How it works
------------
Vestigo currently supports three modes of reading a Bluetooth device:

- Discoverable
	- A Bluetooth device that is configured as discoverable.
- Non-Discoverable
	- A Bluetooth device that accepts connections but is not Broadcasting itself
- Low Energy (BLE)
	- A Bluetooth 4.0 Low Energy device that is discoverable

Discoverable and BLE devices return an standard RSSI where-as Non-Discoverable devices currently only return their golden receive power range (GRPR). It is important to note that Vestigo does not attempt to pair with any devices (unless it's non-discoverable, in which case it continuously attempts to connect, to obtain the device's GRPR, but it will never successfully pair).

There are two sets up scripts. One set: `Vestigo`, is meant to be run on the reading devices, and the other set: `Vestigo Base` is meant to be run on a central server that each reader can connect to. I've been using Raspberry Pi's as cheap readers with a WiFi and Bluetooth adapter and they work great.

On the base server, you will be able to configure the location rules that associate a device's RSSI or GRPR to a corresponding location identifier through the definition of RSSI/GRPR thresholds.

Configuration
-------------
### Vestigo (Reader)

Vestigo has one configuration file: `Vestigo\vestigo.ini`.
This configuration file allows the user to 

- Enable/disable scan modes (BLE, Discoverable, Non-Discoverable)
	*It is important to note that enabling all scan modes at once is with no timeouts is discouraged as I've noticed it tends to bog down most adapters I've tested with
- Define read timeouts - seconds between each attempt to read
- Configure base server host, request timeout and rechace period in seconds (period between each request for updated assets)
- Configure logging

### Vestigo Base (Server)
Vestigo Base has one configuration file: `Vestigo Base\vestigo.ini`.
This configuration file allows the user to 

- Define listen port for HTTP server
- Define URL to forward all data to (useful if you want to write a web application that uses WebSockets and not have to poll the server, or if you want to store the data to a database)
- Set recache period in seconds, for reloading locations and assets
- Configure logging

To configure assest and location rules, edit the JSON located in: `Vestigo Base\addresses.cfg` and `Vestigo Base\locations.cfg`

### Vestigo Base Web Server

The Vestigo Base web server allows you to poll it for asset state information using the following request: http://HOST:PORT/states. It's states will be returned in JSON.

I made a simple web application that servers up all the content in `Vestigo Base\web\` to a browser when a request is made to it's host with no parameters: http://HOST:PORT

The web application allows you to provide a blueprint image: `Vestigo Base\web\blueprint.png` and configure locations to coordinates on that image through the use of the `Vestigo Base\web\coords.cfg` file.

Hardware
--------
For testing I used a series of Model B Raspberry Pis as readers. I am running Raspbian on each of them, but have also tested it with Arch. The adapter I find that works the best for the Raspberry Pi (requires no drivers on Raspbian) and supports Bluetooth 4.0 is the Plugable USB-BT4LE Bluetooth 4.0 USB Adapter.

I am currently using a series of Raspberry Pis to track my iPad and iPhone (non-discoverable devices with Bluetooth enabled), and a set of Stick N' Find BLE tags, throughout my house using a series of nested location rules with appropriate RSSI/GRPR thresholds.

How to install it
-----------------
To install the Vestigo reader on a Raspberry Pi running Raspbian, follow these steps:

Install the Bluetooth support package

    apt-get install bluetooth

Verify the bluetooth daemon is running
	
    /etc/init.d/bluetooth status

Verify your adapter is recognized
	
	hcitool dev

Install hcidump
	
	apt-get install bluez-hcidump

Install python library "requests"
Using easy_install: 

	easy_install install requests

or using pip: 

	pip install requests


That's it!

To start the reader run

	python vestigo.py

To start the base server run

	python vestigo_base.py


Remember to add devices to the addresses.cfg file. An easy way to find an address of a device is to use 
	
	hcitool scan

for discoverable devices, or 

    hcitool lescan

for BLE devices. For non-discoverable devices, put them into discoverable (such as opening up the bluetooth screen on iOS), and then capture their address before making them non-discoverable.

Future features
---------------
I have a load of features and enhancements I'd like to add to this project when I find more time. Here is a list of some that I'd like to add:
- Location timeouts
- Proper daemonization of the reader and server processes
- WebSocket based web application demo
- Normalization modules for different types of device adapters and reader adapters. Allowing you to relationally skew the incoming SSI of each device based on the reader and devices adapter (since different types of adapters give off different SSI readings)
- Research better means for getting a more accurate distance read of devices. Factor in Link Query?
- Triangulation...oh boy
