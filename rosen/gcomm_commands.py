from datetime import datetime
from dateutil.tz import gettz

from rosen.gcomm import GCOMM
from rosen.icomm import ICOMM
from rosen.axe import AXE

def sdcard(*args):
    if args[0] == 'enable':
        return GCOMM('enable_sd')
    elif args[0] == 'disable':
        return GCOMM('disable_sd')
    elif args[0] == 'list':
        return GCOMM('list_sd')
    elif args[0] == 'down':
        return GCOMM('down_file', filename=args[1])
    elif args[0] == 'rm':
        return GCOMM('rm_file', filename=args[1])
    elif args[0] == 'exec':
        return GCOMM('exec_file', filename=args[1])
    elif args[0] == 'clear':
        if len(args) > 1 and args[1] == 'Yes':
            return GCOMM('clear_sd')
        else:
            return False
    elif args[0] == 'info':
        return GCOMM('file_sd', filename=args[1])
    elif args[0] == 'abort':
        return GCOMM('abort_script')
    else:
        return False

def time(*args):
    if args[0] == 'get':
        return GCOMM('get_time')
    elif args[0] == 'set':
        t = datetime.now(gettz('America/Chicago')).timestamp()
        t = round(t)
        return GCOMM('set_time', time=t)

def radcom(*args):
    if args[0] == 'reset':
        return GCOMM('reset_radcom')
    else:
        return False
