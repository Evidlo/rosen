#!/usr/bin/env python3

import pytest

from rosen.icomm import ICOMM, ICOMMScript
from rosen.axe import AXE
from rosen.gcomm import GCOMM, GCOMMScript
from rosen.common import handle_time

from datetime import datetime
import os

# ----- AXE -----

def test_axe_parsebuild():
    b = AXE('execute', 'foobar').build()
    a = AXE.parse(b)
    assert a.cmd == 'execute'
    assert a.data == 'foobar'

# ----- ICOMM -----

def test_icomm():
    # manually build an ICOMM packet and parse it
    b = ICOMM('route', 'ground', 'dcm', 0, 0, AXE('execute', 'foobar')).build()
    i = ICOMM.parse(b)
    assert i.cmd == 'route'
    assert type(i.payload) is AXE
    assert i.payload.cmd == 'execute'

    try:
        str(i)
    except Exception:
        pytest.fail("ICOMM printing failed")

def test_icommscript():
    # build a basic ICOMM script
    i_scr = ICOMMScript()
    i_scr.execute('eduplsb', 'foo_command')
    i_scr.statement('eduplsb', foo=[1, 2, 3])
    i_scr.query('eduplsb', [1, 2, 3, 4])
    i_scr.set('qcb', bar=123)

    # check size of script and timestamps
    assert len(i_scr.script) == 4, "Incorrect script length"
    assert i_scr.script[1][0] > i_scr.script[0][0]
    # check ICOMM packet N and M
    for n, (offset, i) in enumerate(i_scr):
        assert i.n == n, "Incorrect ICOMM N field"
        assert i.m == len(i_scr.script), "Incorrect ICOMM M field"

    try:
        str(i_scr)
    except Exception:
        pytest.fail("ICOMMScript printing failed")

# ----- GCOMM -----

def test_gcomm():
    # manually build a gcomm packet and parse it
    i = ICOMM('route', 'ground', 'dcm', 0, 0, AXE('execute', 'foobar'))
    g = GCOMM(
        'exec_now', filename='foobar.txt', n=0, m=100, offset=1234567890,
        addr='0.0.0.0', time=1234567890, errcode=1, errstr='this is an err', packet=i
    )
    GCOMM.parse(g.build())

    # build other packets
    g = GCOMM('ok', addr='0.0.0.0')
    GCOMM.parse(g.build())
    g = GCOMM('ok')
    GCOMM.parse(g.build())

    # test string representation
    try:
        str(g)
    except Exception:
        pytest.fail("GCOMM printing failed")

def test_gcommscript_commands():
    # build a basic GCOMM script
    g_scr = GCOMMScript()
    i = ICOMM('route', 'ground', 'dcm', 0, 0, AXE('execute', 'foobar'))
    g_scr.exec_now(i)
    g_scr.abort_script()
    g_scr.app_file(
        'foo.txt', 5, 100, 1234567890,
        ICOMM('route', 'ground', 'dcm', 0, 0, AXE('execute', 'foobar'))
    )
    assert g_scr.script[-1].n == 5, "Incorrect GCOMM N field"
    assert g_scr.script[-1].m == 100, "Incorrect GCOMM N field"
    g_scr.rm_file('foo.txt')
    g_scr.exec_file('foo.txt')
    g_scr.down_file('foo.txt')
    g_scr.list_sd()
    g_scr.clear_sd()
    g_scr.disable_sd()
    g_scr.enable_sd()
    g_scr.set_addr('0.0.0.0')
    g_scr.get_time()
    g_scr.set_time(1234567890)
    g_scr.reset_radcom()
    g_scr.ok()
    g_scr.nok(1337, 'This is an error message')
    g_scr.file_sd('foo.txt')

    assert len(g_scr.script) == 17, "Incorrect GCOMM script length"

    # test string representation
    try:
        str(g_scr)
    except Exception:
        pytest.fail("GCOMMScript printing failed")

def test_gcommscript_helpers(tmpdir):
    # test helper methods on GCOMMScript for uploading/scheduling ICOMMScripts
    i = ICOMMScript()
    i.execute('eduplsb', 'foobar')
    i.execute('eduplsb', 'foobar')
    i.execute('eduplsb', 'foobar')

    g_scr = GCOMMScript()
    g_scr.upload_script('test_script', i)
    assert len(g_scr.script) == 3, "Incorrect GCOMM script length"

    g_scr.schedule_script(1234567890, i)
    assert len(g_scr.script) == 6, "Incorrect GCOMM script length"

    g_scr.save('script.pkl')
    g_scr = GCOMMScript.load('script.pkl')
    assert len(g_scr.script) == 6, "Incorrect GCOMM script length"

    try:
        str(g_scr)
    except Exception:
        pytest.fail("GCOMMScript printing failed")

# ----- Common functions -----

def test_handle_time():
    handle_time('2023-01-01')
    handle_time(datetime(2023, 1, 1))
    handle_time(1234567890)
