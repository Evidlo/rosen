# Groundstation

This repo contains the ground station software to be run on a Nanoracks ground station machine for communicating with SEAQUE as well as functions for generating scripts to send to the ground station.

    pip install -e .
    
## Protocol Summary

- GCOMM - Communication between ground station and RADCOM
  - Usually contains an ICOMM packet, unless we are directly telling RADCOM to do something, like reboot
- ICOMM - Communication between RADCOM and various payloads
  - Can be scheduled to be delivered to payloads at specific times.  This is how payload scripts are written.
- AXE - Actions executed by payloads, like setting/getting variables or running internal routines.
    
## Creating and Saving Scripts

``` python
from datetime import date
from rosen.icomm import ICOMMScript
from rosen.gcomm import GCOMMScript

# ----- Script 1 -----

s1 = ICOMMScript()
s1.execute('eduplsb', 'foo_command')
s1.statement('eduplsb', foo=[1, 2, 3])
# query thermistor values on dcm payload
s1.query('dcm', ['thermistor1', 'thermistor2'])
s1.set('qcb', bar=123)

# ----- Script 2 -----

# control the time to wait between actions (seconds)
s2 = ICOMMScript(increment=2)
# wait 5 seconds between each action
s2.increment = 5
for i in range(100):
    s2.set('qcb', bar=i)
    
# ----- Schedule/Upload Scripts -----

g = GCOMMScript()
# upload and schedule the ICOMM script above to run at specific time
g.schedule_script(0, s1)
# upload the script to a file on the SD card
g.upload_script('testfile', s2)
# also can send other GCOMM commands here
g.reset_radcom()
g.exec_file('testfile')

# save GCOMM script to file to be sent to Nanoracks
g.save('myscript.pkl')
```

## Manually Building/Parsing ICOMM and AXE Packets

``` python
from rosen.icomm import ICOMM
from rosen.axe import AXE

a = AXE('execute', 'foo_command')
print(a)
# execute(foo_command)
b = a.build()
print(b)
# b'!.\x00\xabfoo_command'
print(AXE.parse(b))
# execute(foo_command)

i = ICOMM('route', 'ground', 'dcm', 0, 0, a)
print(i)
# ground→dcm: execute(foo_command)
b = i.build()
print(b)
# b'\x00\x18\x01\x02\x05\x00\x00!.\x00\xabfoo_command@\xae\x86\xd6'
print(ICOMM.parse(b))
# dcm→ground: execute(foo_command)
```

## Running Client and Server

Run the client and send GCOMM commands from file.  See `rosen -h` for host/port configuration

    $ rosen run myscript.pkl --loop
    
There is also a test server that responds with GCOMM `OK` packets to everything

    $ rosen server

## Running Tests

    $ pytest rosen
