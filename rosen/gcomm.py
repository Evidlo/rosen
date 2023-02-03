#!/usr/bin/env python3

from construct import (
    Bytes, Byte, PaddedString, Struct, Int32ub, ExprAdapter, Mapping,
    Default, GreedyBytes
)
import pickle

def bytes2ip(b, *args):
    return '.'.join(map(str, b))
def ip2bytes(ip, *args):
    return bytes(map(int, ip.split('.')))

# ----- Command definitions -----

gcomm = Struct(
    "cmd" / Mapping(
        Byte,
        {
            'exec_now':1, 'abort_script':2, 'app_file':3, 'rm_file':4,
            'exec_file':5, 'down_file':6, 'list_sd': 7, 'clear_sd':8,
            'disable_sd':9, 'enable_sd':10, 'set_addr':11, 'get_time':12,
            'set_time':13, 'reset_radcom':14, 'ok':15, 'nok':16
        }
    ),
    "filename" / Default(PaddedString(16, 'ascii'), ''),
    "n" / Default(Int32ub, 0),
    "m" / Default(Int32ub, 0),
    "offset" / Default(Int32ub, 0),
    "addr" / Default(ExprAdapter(Bytes(4), bytes2ip, ip2bytes), '0.0.0.0'),
    "time" / Default(Int32ub, 0),
    "err" / Default(PaddedString(32, 'ascii'), ''),
    "script" / Default(GreedyBytes, b'')
)

class GCOMMScript:

    def __init__(self):
        # list of bytestrings containing GCOMM commands
        self.script = []

    # ----- GCOMM Commands -----

    def exec_now(self, script):
        """Generate GCOMM EXEC_NOW command

        Args:
            script (bytes):
        """
        self.script.append(gcomm.build({'cmd':'exec_now', 'script':script}))

    def abort_script(self):
        """Generate GCOMM ABORT_SCRIPT command """
        self.script.append(gcomm.build({'cmd':'abort_script'}))

    def app_file(self, filename, n, m, offset, script):
        """Generate GCOMM APP_FILE command"""
        self.script.append(
            gcomm.build({
                'cmd':'app_file', 'filename':filename, 'n':n, 'm':m,
                'offset':offset, 'script':script
        }))

    def rm_file(self, filename):
        """Generate GCOMM RM_FILE command """
        self.script.append(gcomm.build({'cmd':'rm_file', 'filename':filename}))

    def exec_file(self, filename):
        """Generate GCOMM EXEC_FILE command """
        self.script.append(gcomm.build({'cmd':'exec_file', 'filename':filename}))

    def down_file(self, filename):
        """Generate GCOMM DOWN_FILE command """
        self.script.append(gcomm.build({'cmd':'down_file', 'filename':filename}))

    def list_sd(self):
        """Generate GCOMM LIST_SD command """
        self.script.append(gcomm.build({'cmd':'list_sd'}))

    def clear_sd(self):
        """Generate GCOMM CLEAR_SD command """
        self.script.append(gcomm.build({'cmd':'clear_sd'}))

    def disable_sd(self):
        """Generate GCOMM DISABLE_SD command """
        self.script.append(gcomm.build({'cmd':'disable_sd'}))

    def enable_sd(self):
        """Generate GCOMM ENABLE_SD command """
        self.script.append(gcomm.build({'cmd':'enable_sd'}))

    def set_addr(self, addr):
        """Generate GCOMM SET_ADDR command """
        self.script.append(gcomm.build({'cmd':'set_addr', 'addr':addr}))

    def get_time(self):
        """Generate GCOMM GET_TIME command """
        self.script.append(gcomm.build({'cmd':'get_time'}))

    def set_time(self, time):
        """Generate GCOMM SET_TIME command """
        self.script.append(gcomm.build({'cmd':'set_time', 'time':time}))

    def reset_radcom(self):
        """Generate GCOMM RESET_RADCOM command """
        self.script.append(gcomm.build({'cmd':'reset_radcom'}))

    def ok(self):
        """Generate GCOMM OK command """
        self.script.append(gcomm.build({'cmd':'ok'}))

    def nok(self, errcode, errstr):
        """Generate GCOMM NOK command """
        self.script.append(gcomm.build(
            {'cmd':'nok', 'errcode':errcode, 'errstr':errstr}
        ))


    # ----- Helper Functions -----

    def schedule_script(self, time, axe_script):
        """Helper func to upload an AXE script and schedule it at a specific time

        Args:
            time (int): time to run script in seconds since epoch
            script (AXEScript): AXE script to upload
        """
        f = str(time)
        assert len(f) <= 13, "Filename must be 13 or less characters"
        for n, (offset, icomm_bytes) in enumerate(axe_script.script):
            self.app_file(str(time), n, len(axe_script.script), offset, icomm_bytes)

    def upload_script(self, f, axe_script):
        """Helper func to upload an AXE script and schedule it at a specific time

        Args:
            f (str): filename of new script
            script (AXEScript): AXE script to upload
        """
        self.schedule_script(f, axe_script)

    def save(self, filename):
        """Save GCOMM script as pickle file

        Args:
            filename (str): file to output to
        """
        with open(filename, 'wb') as f:
            pickle.dump(self.script, f)
