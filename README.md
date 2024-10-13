# Overview

Simple Python library to control the [TP-Link Kasa Smart Power Strip (HW 1.0)](https://www.amazon.com/Smart-Wi-Fi-Power-Strip-TP-Link/dp/B07G95FFN3/)

The command syntax is fairly similar to the single relay TP-Link smart plugs 

Encrypt/Decrypt code is based on https://github.com/softScheck/tplink-smartplug/blob/master/tplink_smartplug.py

The main difference seems to be that the basic get_sysinfo command only works over UDP, all other commands
can use either UDP or TCP

If working with Python 2.7 you must ensure the future package is installed.

```bash
$ pip install future
```

Also now compatible with [Adafruit CircuitPython](https://circuitpython.org/) under the [CircuitPython branch](https://github.com/p-doyle/Python-KasaSmartPowerStrip/tree/CircuitPython).

## Example code:

```python
from KasaSmartPowerStrip import SmartPowerStrip

power_strip = SmartPowerStrip('<your power strip ip>')

# get general system info
print(power_strip.get_system_info())

# get the name and other info of a plug; unless the Kasa app is used the plugs won't have a name by default
print(power_strip.get_plug_info(1))

# set the name of a plug
print(power_strip.set_plug_name(1, 'my plug'))

# toggle a plug by number (1-6)
print(power_strip.toggle_plug('off', plug_num=1))

# toggle a plug by name
print(power_strip.toggle_plug('on', plug_name='my plug'))

# toggle multiple plugs by number
print(power_strip.toggle_plugs('on', plug_num_list=[1, 3, 5]))

# toggle multiple plugs by name
print(power_strip.toggle_plugs('on', plug_name_list=['my plug', 'my plug 2']))

# toggle the LEDs for each relay on or off
print(power_strip.toggle_relay_leds('off'))

# get the current energy usage with mA, mV, mW, and the total wh
print(power_strip.get_realtime_energy_info(plug_num=1))

# get a list with the watt-hours for each day in the specified month/year
print(power_strip.get_historical_energy_info(month='10', year='2018', plug_num=1))

# reboot the power strip
# NOTE this will toggle all relays off/on but will preserve state after rebooting
# e.g. if it was off before rebooting it will remain off afterward
print(power_strip.reboot(5))
```

## Initial Setup
To set up a new power strip without having to use the Kasa App(which requires you to create a cloud account):
1. Plug the power strip in and ensure that the status LED is alternating green/orange.  If it isn't pressed and
    hold one of the relay buttons for 5 seconds to perform a factory reset.
2. Look for and connect to a WiFi network which should start with TP-LINK_Power Strip.
    The default IP of the power strip is 192.168.0.1.  It will only accept commands from IP 192.168.0.100, which
    it should be assigned to the first device to connect to its WiFi.
3. OPTIONAL: If you want to ensure that the power strip never connects to the cloud there are a few options.
    The first is to clear the cloud server URL that is set on the power strip but I can't guarantee that this works.
    UPDATE: It seems setting the server_url blank does not work and the device will still attempt to connect to n-devs.tplinkcloud.com. I would recommend using something like [PiHole](https://github.com/pi-hole/pi-hole) for DNS where you can blacklist n-devs.tplinkcloud.com to prevent the switch from resolving it to an IP address.
   
    The second option is to get the MAC address of the power strip so that you can block outgoing traffic on your 
    router before allowing it to connect to your network or use VLANs to prevent it from connecting to the internet
    If it has no internet access however it will be constantly making NTP requests, which may be required for the historical usage data to work correctly, though I can't say for sure. 

```python
power_strip = SmartPowerStrip('192.168.0.1')

print(power_strip.set_cloud_server_url(server_url=''))

print(power_strip.get_system_info()['system']['get_sysinfo']['mac'])
```

4. Use the below code to have it connect to your own WiFi network:

```python
power_strip = SmartPowerStrip('192.168.0.1')

# For WPA2 the key_type is '3', I would guess WPA is '2' and WEP is '1' but I have not tested this
power_strip.set_wifi_credentials('my ssid', 'my psk', key_type='3')
```

NOTE: After WiFi is provisioned the device will reboot and connect to the WiFi on startup. The device should be usable after reboot.
## Other commands not yet implemented:

Add countdown timer rules:
```json
{"context":{"child_ids":["<plug childId>"]},"count_down":{"add_rule":{"act":1,"delay":1800,"enable":1,"name":"add timer"}}}
```

Get countdown timer rules:
```json
{"context":{"child_ids":["<plug childId>"]},"count_down":{"get_rules":{}}}
```

Delete countdown timer rules:
```json
{"context":{"child_ids":["<plug childId>"]},"count_down":{"delete_all_rules":{}}}
```
