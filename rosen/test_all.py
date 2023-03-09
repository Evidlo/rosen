#!/usr/bin/env python3

from rosen.icomm import ICOMM, ICOMMScript
from rosen.axe import AXE
from rosen.gcomm import GCOMM, GCOMMScript
from rosen.common import handle_time

from datetime import datetime
import os

def test_axe_parsebuild():
    b = AXE('execute', 'foobar').build()
    a = AXE.parse(b)
    assert a.cmd == 'execute'
    assert a.data == 'foobar'

def test_icomm_parsebuild():
    b = ICOMM('route', 'ground', 'dcm', AXE('execute', 'foobar')).build()
    i = ICOMM.parse(b)
    assert i.cmd == 'route'
    assert type(i.payload) is AXE
    assert i.payload.cmd == 'execute'

def test_commscript():
    # build a basic ICOMM script
    s = ICOMMScript()
    s.execute('eduplsb', 'foo_command')
    s.statement('eduplsb', foo=[1, 2, 3])
    s.query('eduplsb', [1, 2, 3, 4])
    s.set('qcb', bar=123)

    # check size of script and timestamps
    assert len(s.script) == 4, "Incorrect script length"
    assert s.script[1][0] > s.script[0][0]

def test_gcomm_parsebuild():
    # manually build a gcomm packet and parse it
    i = ICOMM('route', 'ground', 'dcm', AXE('execute', 'foobar'))
    b = GCOMM(
        'exec_now', filename='foobar.txt', n=0, m=100, offset=1234567890,
        addr='0.0.0.0', time=1234567890, errcode=1, errstr='this is an err', packet=i
    ).build()
    GCOMM.parse(b)

def test_gcommscript_commands():
    # build a basic GCOMM script
    g = GCOMMScript()
    g.exec_now(b'command')
    g.abort_script()
    g.app_file(
        'foo.txt', 0, 100, 1234567890,
        ICOMM('route', 'ground', 'dcm', AXE('execute', 'foobar'))
    )
    g.rm_file('foo.txt')
    g.exec_file('foo.txt')
    g.down_file('foo.txt')
    g.list_sd()
    g.clear_sd()
    g.disable_sd()
    g.enable_sd()
    g.set_addr('0.0.0.0')
    g.get_time()
    g.set_time(1234567890)
    g.reset_radcom()
    g.ok()
    g.nok(1337, 'This is an error message')

    assert len(g.script) == 16, "Incorrect GCOMM script length"

def test_gcommscript_helpers(tmpdir):
    # build a GCOMM script that uploads an AXE script
    i = ICOMMScript()
    i.execute('eduplsb', 'foobar')
    i.execute('eduplsb', 'foobar')
    i.execute('eduplsb', 'foobar')

    g = GCOMMScript()
    g.schedule_script(1234567890, i)
    assert len(g.script) == 3, "Incorrect GCOMM script length"

    g.upload_script('test_script', i)
    assert len(g.script) == 6, "Incorrect GCOMM script length"

    g.save('script.pkl')
    g = GCOMMScript.load('script.pkl')
    assert len(g.script) == 6, "Incorrect GCOMM script length"

def test_handle_time():
    handle_time('2023-01-01')
    handle_time(datetime(2023, 1, 1))
    handle_time(1234567890)
