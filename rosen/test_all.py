#!/usr/bin/env python3

from rosen.axe import axe, icomm, AXEScript
from rosen.gcomm import gcomm, GCOMMScript

def test_axe_parsebuild():
    # manually build an axe command and parse it
    b = axe.build({'cmd':'execute', 'table':'.', 'data':[]})
    axe.parse(b)

def test_icomm_parsebuild():
    # manually build an icomm packet and parse it
    b = icomm.build(
        {'body':{'value':
            {'cmd':'route', 'to':'eduplsb', 'from':'ground', 'payload':b'hello'}
        }}
    )
    icomm.parse(b)

def test_axescript():
    # build a basic AXE script
    a = AXEScript()
    a.execute('eduplsb', 'foo_command')
    a.statement('eduplsb', foo=[1, 2, 3])
    a.query('eduplsb', [1, 2, 3, 4])
    a.set('qcb', bar=123)

    # check size of script and timestamps
    assert len(a.script) == 4, "Incorrect script length"
    assert a.script[1][0] > a.script[0][0]

def test_gcomm_parsebuild():
    # manually build a gcomm packet and parse it
    b = gcomm.build({
        'cmd':'exec_now', 'filename':'foobar.txt', 'n':0, 'm':100,
        'offset':1234567890, 'addr':'0.0.0.0', 'time':1234567890,
        'err':'this is an error', 'script':b'hello world'
    })
    gcomm.parse(b)

def test_gcommscript_commands():
    # build a basic GCOMM script
    g = GCOMMScript()
    g.exec_now(b'command')
    g.abort_script()
    g.app_file('foo.txt', 0, 100, 1234567890, b'hello')
    assert g.script[-1][-5:] == b'hello', "Problem with app_file"
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
    a = AXEScript()
    a.execute('eduplsb', 'foobar')
    a.execute('eduplsb', 'foobar')
    a.execute('eduplsb', 'foobar')

    g = GCOMMScript()
    g.schedule_script(1234567890, a)
    assert len(g.script) == 3, "Incorrect GCOMM script length"

    g.upload_script('test_script', a)
    assert len(g.script) == 6, "Incorrect GCOMM script length"

    f = tmpdir.mktemp('output.pkl')
    g.save(f)
