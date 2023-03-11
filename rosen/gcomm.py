#!/usr/bin/env python3

from construct import (
    Bytes, Byte, PaddedString, Struct, Int8ub, Int32ub, ExprAdapter, Mapping,
    Default, GreedyBytes
)
from dataclasses import dataclass
import pickle
from rich.table import Table, Column
from rich.console import Console

from rosen.icomm import ICOMMScript, ICOMM
from rosen.common import handle_time

def bytes2ip(b, *args):
    return '.'.join(map(str, b))
def ip2bytes(ip, *args):
    return bytes(map(int, ip.split('.')))

gcomm_construct = Struct(
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
    "errcode" / Default(Int8ub, 0),
    "errstr" / Default(PaddedString(32, 'ascii'), ''),
    "packet" / Default(GreedyBytes, b'')
)

@dataclass
class GCOMM:
    """Class for building/parsing GCOMM packet"""

    cmd: str
    filename: str = ''
    n: int = 0
    m: int = 0
    offset: int = 0
    addr: str = ''
    time: int = 0
    errcode: int = 0
    errstr: str = ''
    packet: ICOMM = None

    # def __init__(self, cmd=None, filename='', n=None, m=None, offset=None,
    #              addr=None, time=None, errcode=None, errstr=None, packet=None):
    #     """Initialize GCOMM object"""
    #     self.cmd, self.filename, self.n, self.m = cmd, filename, n, m
    #     self.offset, self.addr, self.time, self.errcode = offset, addr, time, errcode
    #     self.errstr, self.packet = errstr, packet

    # def __repr__(self):
    #     """GCOMM string represenetation"""
    #     return "GCOMM"

    def build(self):
        """Build bytes for GCOMM packet

        Returns:
            bytes
        """
        return gcomm_construct.build(dict(
            cmd=self.cmd, filename=self.filename, n=self.n, m=self.m,
            offset=self.offset, addr=self.addr, time=self.time, errcode=self.errcode,
            errstr=self.errstr, packet=self.packet.build()
        ))

    @classmethod
    def parse(cls, raw_bytes):
        """Parse bytes into GCOMM packet object
        Args:
            raw_bytes (bytes): bytestring to parse
        Returns:
            GCOMM instance
        """
        g = gcomm_construct.parse(raw_bytes)
        return cls(
            g.cmd, g.filename, g.n, g.m, g.offset, g.addr, str(g.time),
            str(g.errcode), g.errstr, str(g.packet)
        )


class GCOMMScript:

    def __init__(self, name=''):
        # list of bytestrings containing GCOMM commands
        self.script = []
        self.name = name

    def __repr__(self):
        """Tabular text representation of GCOMM script"""

        table = Table(
            "Command", "Filename", "N", "M", "Offset", "Address", "Time",
            "Errcode", "Errstr",
            Column("Command", style='magenta', header_style='magenta'),
            Column("From", style='magenta', header_style='magenta'),
            Column("To", style='magenta', header_style='magenta'),
            Column("N", style='magenta', header_style='magenta'),
            Column("M", style='magenta', header_style='magenta'),
            Column("AXE", style='green', header_style='green'),
            title=f"GCOMMScript: {self.name}",
        )

        for g in self.script:
            table.add_row(
                g.cmd, g.filename,
                str(g.n or ''), str(g.m or ''),
                str(g.offset or ''),
                g.addr,
                str(g.time or ''),
                str(g.errcode or ''), str(g.errstr or ''),
                g.packet.cmd if g.packet else '',
                g.packet.frm if g.packet else '',
                g.packet.to if g.packet else '',
                str(g.packet.n or '') if g.packet else '',
                str(g.packet.m or '') if g.packet else '',
                str(g.packet.payload) if g.packet else '',
            )

        console = Console()
        with console.capture() as capture:
            console.print(table)

        return capture.get()

    # ----- GCOMM Commands -----

    def exec_now(self, packet):
        """Generate GCOMM EXEC_NOW command

        Args:
            packet (ICOMM or ICOMMScript): if ICOMMScript, execute first ICOMM packet now
        """
        if type(packet) is ICOMMScript:
            assert len(script) == 0, "ICOMMScript can only have one packet when used with 'exec_now'"
            packet = packet.script[0][1]
        self.script.append(GCOMM('exec_now', packet=packet))

    def abort_script(self):
        """Generate GCOMM ABORT_SCRIPT command """
        self.script.append(GCOMM('abort_script'))

    def app_file(self, filename, n, m, offset, packet):
        """Generate GCOMM APP_FILE command"""
        assert len(filename) <= 12, "Filename must not be more than 12 characters"
        self.script.append(GCOMM(
            'app_file', filename=filename, n=n, m=m, offset=offset, packet=packet
        ))

    def rm_file(self, filename):
        """Generate GCOMM RM_FILE command """
        self.script.append(GCOMM('rm_file', filename=filename))

    def exec_file(self, filename):
        """Generate GCOMM EXEC_FILE command """
        self.script.append(GCOMM('exec_file', filename=filename))

    def down_file(self, filename):
        """Generate GCOMM DOWN_FILE command """
        self.script.append(GCOMM('down_file', filename=filename))

    def list_sd(self):
        """Generate GCOMM LIST_SD command """
        self.script.append(GCOMM('list_sd'))

    def clear_sd(self):
        """Generate GCOMM CLEAR_SD command """
        self.script.append(GCOMM('clear_sd'))

    def disable_sd(self):
        """Generate GCOMM DISABLE_SD command """
        self.script.append(GCOMM('disable_sd'))

    def enable_sd(self):
        """Generate GCOMM ENABLE_SD command """
        self.script.append(GCOMM('enable_sd'))

    def set_addr(self, addr):
        """Generate GCOMM SET_ADDR command """
        self.script.append(GCOMM('set_addr', addr=addr))

    def get_time(self):
        """Generate GCOMM GET_TIME command """
        self.script.append(GCOMM('get_time'))

    def set_time(self, time):
        """Generate GCOMM SET_TIME command """
        time = handle_time(time)
        self.script.append(GCOMM('set_time', time=time))

    def reset_radcom(self):
        """Generate GCOMM RESET_RADCOM command """
        self.script.append(GCOMM('reset_radcom'))

    def ok(self):
        """Generate GCOMM OK command """
        self.script.append(GCOMM('ok'))

    def nok(self, errcode, errstr):
        """Generate GCOMM NOK command """
        self.script.append(GCOMM('nok', errcode=errcode, errstr=errstr))


    # ----- Helper Functions -----
    # These are convenience functions built on top of the GCOMM commands shown above

    def schedule_script(self, time, i):
        """Helper func to upload an AXE script and schedule it at a specific time

        Args:
            time (str, int, or datetime.datetime): time to execute the script.
                Defaults to UTC
            i (ICOMMScript): ICOMM script to upload
        """

        filename = str(handle_time(time))
        self.upload_script(filename, i)

    def upload_script(self, filename, i):
        """Helper func to upload an AXE script to a specific file name

        Args:
            filename (str): filename of new script
            i (ICOMMScript): ICOMM script to upload
        """
        assert len(filename) <= 12, "Filename must not be more than 12 characters"
        for n, (offset, icomm_packet) in enumerate(i.script):
            self.app_file(
                filename, n, len(i.script), offset, icomm_packet.build
            )

    def save(self, filename):
        """Save GCOMM script as pickle file

        Args:
            filename (str): file to output to
        """
        with open(filename, 'wb') as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, filename):
        with open(filename, 'rb') as f:
            return pickle.load(f)
