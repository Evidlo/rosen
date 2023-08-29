# Groundstation

This repo contains the ground station software to be run on a ground station machine for communicating with SEAQUE as well as functions for generating scripts to send to the ground station.

    pip install -e .
    
## Protocol Summary

- GCOMM - Communication between ground station and RADCOM
  - Usually contains an ICOMM packet, unless we are directly telling RADCOM to do something, like reboot
  - Can be used to schedule ICOMM packets to be delivered to payloads at specific times.  This is how payload scripts are written.
- ICOMM - Communication between RADCOM and various payloads
- AXE - Actions executed by payloads, like setting/getting variables or running internal routines.

See [SEAQUE_Protocol_Spec.docx](https://uillinoisedu.sharepoint.com/:w:/s/Gambit/Ead1y8GhTDdDpPL6pMAykbYBchad07YlAGAax6WgWh3yvQ?e=JvjfS6) for more details.
    
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
g.schedule_script('2024-06-01', s1)
# upload the script to a file on the SD card
g.upload_script('testfile', s2)
# also can send other GCOMM commands here
g.reset_radcom()
g.exec_file('testfile')

# save GCOMM script to file to be sent
g.save('myscript.pkl')
```

## Manually Building/Parsing GCOMM, ICOMM and AXE Packets

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

g = GCOMM('exec_now', packet=i)
b = g.build()
print(len(b))
# 4162
print(GCOMM.parse(b))
# GCOMM(exec_now, addr=0.0.0.0, packet=ICOMM(route, frm=dcm, to=ground, payload=execute(foo_command)))
```

## Inspecting Packets

All packet and script classes have pretty printing to ease inspection

``` python
from rosen.axe import AXE
from rosen.icomm import ICOMMScript, ICOMM
from rosen.gcomm import GCOMMScript

is1 = ICOMMScript('set up some quantum things')
is1.execute('qcb', 'butterflies')
is1.set('dcm', foo=[1, 2, 3])
is1.query('qcb', ['therm1', 'therm2'])
print(is1)
#            ICOMMScript: set up some quantum things             
# ┏━━━━━━━━┳━━━━━━┳━━━━━━━━┳━━━┳━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃ Offset ┃ From ┃ To     ┃ N ┃ M ┃ Payload                     ┃
# ┡━━━━━━━━╇━━━━━━╇━━━━━━━━╇━━━╇━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
# │ 0      │ qcb  │ ground │ 0 │ 3 │ execute(butterflies)        │
# │ 1      │ dcm  │ ground │ 1 │ 3 │ set({'foo': [1, 2, 3]})     │
# │ 2      │ qcb  │ ground │ 2 │ 3 │ query(['therm1', 'therm2']) │
# └────────┴──────┴────────┴───┴───┴─────────────────────────────┘

print(is1.script[0])
# (0, ICOMM(route, frm=qcb, to=ground, n=0, m=3, payload=execute(butterflies)))

gs1 = GCOMMScript('week 35 script')
gs1.schedule_script('wednesday', is1)
gs1.exec_now(ICOMM('route', 'ground', 'qcb', 0, 0, AXE('execute', 'laser_start')))
gs1.set_time('2023-01-01 4pm')
gs1.get_time()
print(gs1)
#                                                             GCOMMScript: week 35 script                                                              
# ┏━━━━━━━━━━┳━━━━━━━━━━━━┳━━━┳━━━┳━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━┳━━━━━━━━┳━━━━━━━━┳━━━┳━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃ Command  ┃ Filename   ┃ N ┃ M ┃ Offset ┃ Address ┃ Time       ┃ Errcode ┃ Errstr ┃ Command ┃ From   ┃ To     ┃ N ┃ M ┃ AXE                         ┃
# ┡━━━━━━━━━━╇━━━━━━━━━━━━╇━━━╇━━━╇━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━╇━━━━━━━━╇━━━━━━━━╇━━━╇━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
# │ app_file │ 1678838400 │ 0 │ 3 │ 0      │         │            │         │        │ route   │ qcb    │ ground │ 0 │ 3 │ execute(butterflies)        │
# │ app_file │ 1678838400 │ 1 │ 3 │ 1      │         │            │         │        │ route   │ dcm    │ ground │ 1 │ 3 │ set({'foo': [1, 2, 3]})     │
# │ app_file │ 1678838400 │ 2 │ 3 │ 2      │         │            │         │        │ route   │ qcb    │ ground │ 2 │ 3 │ query(['therm1', 'therm2']) │
# │ exec_now │            │   │   │        │         │            │         │        │ route   │ ground │ qcb    │   │   │ execute(laser_start)        │
# │ set_time │            │   │   │        │         │ 1672588800 │         │        │         │        │        │   │   │                             │
# │ get_time │            │   │   │        │         │            │         │        │         │        │        │   │   │                             │
# └──────────┴────────────┴───┴───┴────────┴─────────┴────────────┴─────────┴────────┴─────────┴────────┴────────┴───┴───┴─────────────────────────────┘
```

## Running Client and Server

Run the client and send GCOMM commands from file.  See `rosen -h` for host/port configuration

    $ rosen run myscript.pkl --loop
    
There is also a test server that responds with GCOMM `OK` packets to everything

    $ rosen server
    
## Running Tests

    $ pytest rosen

## Usage

``` python
[evan@blackbox ~] rosen -h 
usage: rosen [-h] [--debug] [--host HOST] [--port PORT] {run,server} ...

SEAQUE ground station

commands:
  {run,server}
    run         run a GCOMM script file
    server      run a test echo server

options:
  -h, --help    show this help message and exit
  --debug       enable debugging
  --host HOST   SEAQUE host
  --port PORT   SEAQUE port
```
