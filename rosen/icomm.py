#!/usr/bin/env python3

from construct import (
    Checksum, Struct, Int8ub, Int16ub, ExprAdapter, this, Byte, GreedyBytes,
    Mapping, OffsettedEnd, Prefixed, Bytes, CString,
    VarInt, RawCopy, Probe, Padded
)
from dataclasses import dataclass
from msgpack import packb, unpackb
from rich.console import Console
from rich.table import Table
import binascii

from rosen.axe import AXE
from rosen.common import Script, Packet, MutInt

device_map = Mapping(
    Byte,
    {
        'albin': 1,
        'dcm': 2,
        'qcb': 3,
        'eduplsb': 4,
        'ground': 5,
        'radcom': 6
    }
)

icomm_construct = Padded(
    4092,
    Prefixed(Int16ub, Struct(
        "body" / RawCopy(Struct(
            "cmd" / Mapping(
                Byte,
                # command map
                {
                    'route': 1,
                    'ack': 2,
                    'nack': 3,
                }
            ),
            "to" / device_map,
            "frm" / device_map,
            "n" / Int8ub,
            "m" / Int8ub,
            "payload" / OffsettedEnd(-4, GreedyBytes),
        )),
        "checksum" / Checksum(
            Bytes(4),
            lambda data: binascii.crc32(data).to_bytes(4, 'big'),
            this.body.data
        )
)))

@dataclass(repr=False)
class ICOMM(Packet):
    """Class for building/parsing ICOMM packet"""
    cmd: str
    frm: str
    to: str
    n: int = 0
    m: int|MutInt = 0
    payload: AXE = None

    def build(self):
        """Build bytes for GCOMM packet

        Returns:
            bytes
        """
        axe_bytes = self.payload.build()
        return icomm_construct.build({'body':{'value':
            {
                'cmd':self.cmd, 'to':self.to, 'frm':self.frm, 'n':self.n,
                # accept int or list for length
                # 'm':len(self.m) if hasattr(self, '__len__') else self.m,
                'm':self.m,
                'payload':axe_bytes
            }
        }})

    @classmethod
    def parse(cls, raw_bytes):
        parsed = icomm_construct.parse(raw_bytes)
        return cls(
            parsed.body.value.cmd, parsed.body.value.to, parsed.body.value.frm,
            parsed.body.value.n, parsed.body.value.m,
            AXE.parse(parsed.body.value.payload)
        )


# ----- Scripting -----

class ICOMMScript(Script):

    def __init__(self, name='', offset=0, increment=1):
        """Class for generating ICOMM script sequences

        Args:
            name (str): optional name of script
            offset (float): time offset of next ICOMM packet
            increment (float): seconds to increment offset after new command
        """
        # optional name of the script for printing purposes
        self.name = name
        # starting time offset
        self.offset = offset
        # ICOMM packet number
        self.n = 0
        # total packets
        self.m = MutInt(0)
        # offset time increment after adding a command
        self.increment = increment
        # list of tuples containing (execution_time, icomm_packet)
        self.script = []

    def __repr__(self):
        """Pretty print object as table"""

        table = Table(
            "Offset", "From", "To", "N", "M", "Payload",
            title=f"ICOMMScript: {self.name}",
        )

        for cmd in self.script:
            table.add_row(
                str(cmd[0]), cmd[1].frm, cmd[1].to, str(cmd[1].n),
                str(cmd[1].m), str(cmd[1].payload)
            )

        console = Console()
        with console.capture() as capture:
            console.print(table)

        return capture.get()

    # ----- AXE Helper Functions -----
    # Helper functions for quickly building ICOMM/AXE commands

    def execute(self, device, command, table='.'):
        """Generate ICOMM/AXE 'execute' command

        Args:
            device (str): ICOMM device name
            command (str): AXE command to run on device
            table (bytes): AXE table
        """
        axe_packet = AXE('execute', command, table=table)
        icomm_packet = ICOMM('route', device, 'ground', self.n, self.m, axe_packet)
        self.script.append((self.offset, icomm_packet))
        self.offset += self.increment
        self.n += 1
        self.m += 1

    def query(self, device, items, table='.'):
        """Generate ICOMM/AXE 'query' command

        Args:
            device (str): ICOMM device name
            items (list): AXE items to query on device
            table (bytes): AXE table
        """
        axe_packet = AXE('query', items, table=table)
        icomm_packet = ICOMM('route', device, 'ground', self.n, self.m, axe_packet)
        self.script.append((self.offset, icomm_packet))
        self.offset += self.increment
        self.n += 1
        self.m += 1

    def set(self, device, table='.', **data):
        """Generate ICOMM/AXE 'set' command

        Args:
            device (str): ICOMM device name
            **data (keyword args): AXE items to set on device
            table (bytes): AXE table
        """
        axe_packet = AXE('set', data, table=table)
        icomm_packet = ICOMM('route', device, 'ground', self.n, self.m, axe_packet)
        self.script.append((self.offset, icomm_packet))
        self.offset += self.increment
        self.n += 1
        self.m += 1

    def statement(self, device, table='.', **data):
        """Generate ICOMM/AXE 'statement' command

        Args:
            device (str): ICOMM device name
            **data (keyword args): AXE items in statement
            table (bytes): AXE table
        """
        axe_packet = AXE('statement', data, table=table)
        icomm_packet = ICOMM('route', device, 'ground', self.n, self.m, axe_packet)
        self.script.append((self.offset, icomm_packet))
        self.offset += self.increment
        self.n += 1
        self.m += 1
