from rosen.gcomm import GCOMM
from rosen.icomm import ICOMM
from rosen.axe import AXE
import rosen.gcomm_commands as gccm
import re
import json

gcomm_cmd_table = {
        "sdcard": gccm.sdcard,
        "time": gccm.time,
        "radcom": gccm.radcom
        }

def cmd_parse(string):

    # TODO handle case in-sensitive vars
    args = string.split(' ')
    cmd = args[0]

    try:

        if cmd in {'?', '!', '>', '.'}:
            return exec_now_parse(args)
        elif cmd in gcomm_cmd_table:
            return gcomm_cmd_table[cmd](*args[1:])
        else:
            return False

    except:
        return False



def exec_now_parse(args):


    axe_cmd_tbl = {
            "!":"execute",
            "?":"query",
            ".":"statement",
            ">":"set"
            }

    if len(args) < 2:
        return False

    board = args[1]
    axe_cmd = args[0]

    if board not in {'dcm', 'qcb', 'radcom', 'albin', 'eduplsb'}:
        return False

    if axe_cmd not in {'!', '?', '.', '>'}:
        return False

    if axe_cmd == '.':
        txid = int(args[2])
        data = args[3:]
    else:
        txid = 0
        data = args[2:]

    if not check_valid(axe_cmd, data):
        return False

    parsed = axe_data_parse(axe_cmd, data)

    if parsed == False:
        return False

    return GCOMM('exec_now', packet=ICOMM(cmd='cmd', to=board, frm='ground', payload=AXE(cmd=axe_cmd_tbl[axe_cmd], data=parsed)))

# TODO Checks that there are no invalid characters or formatting
def check_valid(axe_cmd, data):
    return True

def axe_data_parse(axe_cmd, data):
    # For these, it's easier to use regex's to make it json, then parse
    if axe_cmd in {'.', '>'}:
        string = ' '.join(data)
        string = string.replace('=',':')
        string = re.sub('  *', ',', string)
        string = '{' + string + '}'
        # regex to add quotes for json parsing
        string = re.sub(r'(?P<name>[a-zA-Z0-9_]*) *:', '"\g<name>":', string)
        try:
            var = json.loads(string)
        except json.decoder.JSONDecodeError:
            return False

        return var
    # Already should be an array of strings
    elif axe_cmd == '?':
        return data
    # Should be single string
    elif axe_cmd == '!':
        return data[0]
    else:
        raise Exception("Uncaught parse error")

# TODO This function checks the used entries, and makes sure they exist in the desination table, as
# well as are the right data type. Will cast as needed.
def axe_table_check(board, entries):
    return True
