# Python-KasaSmartPowerStrip

Simple Python library to control the TP-Link Kasa Smart Power Strip<br/>
Amazon link: https://www.amazon.com/Smart-Wi-Fi-Power-Strip-TP-Link/dp/B07G95FFN3/

Command syntax is fairly similar to the single relay TP Link smart plugs<br/>
Encrypt/Decrypt code is based on https://github.com/softScheck/tplink-smartplug/blob/master/tplink_smartplug.py<br/>
The main difference seems to be that the basic get_sysinfo command only works over UDP

Example code:

```
from KasaSmartPowerStrip import SmartPowerStrip

power_strip = SmartPowerStrip('<your power strip ip>')

print(power_strip.get_system_info())

print(power_strip.toggle_plug('off', plug_num=1))
print(power_strip.toggle_plug('off', plug_name='Plug 3'))
```

To do:<br>
Implement functionality to get energy stats.  Can get using:<br>
```{"context":{"child_ids":["<plug childId>"]},"emeter":{"get_realtime":{}}}```<br>
  or<br>
```{"context":{"child_ids":["<plug childId>"]},"emeter":{"get_daystat":{"month":8,"year":2018}}}```
  
  
