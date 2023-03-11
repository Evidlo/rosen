#!/usr/bin/env python3

from construct import (
    Checksum, Struct, Int8ub, Int16ub, ExprAdapter, this, Byte, GreedyBytes,
    Mapping, OffsettedEnd, Prefixed, Bytes, CString,
    VarInt, RawCopy, Probe
)
from dataclasses import dataclass
from msgpack import packb, unpackb
from rich.console import Console
from rich.table import Table
import binascii

from rosen.axe import AXE

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

icomm_construct = Prefixed(Int16ub, Struct(
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
))

@dataclass
class ICOMM:
    """Class for building/parsing ICOMM packet"""
    cmd: str
    frm: str
    to: str
    n: int
    m: int
    payload: AXE

    # def __init__(self, cmd=None, to=None, frm=None, n=None, m=None, payload=None):
    #     self.cmd, self.to, self.frm, self.payload=cmd, to, frm, payload

    def __repr__(self):
        """ICOMM string representation"""
        if self.cmd == 'ack':
            p = "ACK"
        elif self.cmd == 'nack':
            p = "NACK"
        else:
            p = self.payload

        return f"{self.frm}→{self.to}: {p}"

    def build(self):
        """Build bytes for GCOMM packet

        Returns:
            bytes
        """
        axe_bytes = self.payload.build()
        return icomm_construct.build({'body':{'value':
            {
                'cmd':self.cmd, 'to':self.to, 'frm':self.frm, 'n':self.n,
                'm':self.m, 'payload':axe_bytes
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

class ICOMMScript:

    def __init__(self, name='', offset=0, increment=1):
        """Class for generating ICOMM script sequences

        Args:
            name (str): optional name of script
            offset (float): time offset of next ICOMM packet
            increment (float): seconds to increment offset after new command
        """
        # optional name of the script for printing purposes
        self.name = name
        # current time offset
        self.offset = offset
        # offset time increment after adding a command
        self.increment = increment
        # list of tuples containing (execution_time, icomm_packet)
        self.script = []

    def __len__(self):
        return len(self.script)

    def __repr__(self):
        """Pretty print object as table"""

        table = Table(
            "Time", "From", "To", "Payload",
            title=f"ICOMMScript: {self.name}",
        )

        for cmd in self.script:
            table.add_row(
                str(cmd[0]), cmd[1].frm, cmd[1].to,
                str(cmd[1].payload))

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
        icomm_packet = ICOMM('route', device, 'ground', 0, 0, axe_packet)
        self.script.append((self.offset, icomm_packet))
        self.offset += self.increment

    def query(self, device, items, table='.'):
        """Generate ICOMM/AXE 'query' command

        Args:
            device (str): ICOMM device name
            items (list): AXE items to query on device
            table (bytes): AXE table
        """
        axe_packet = AXE('query', items, table=table)
        icomm_packet = ICOMM('route', device, 'ground', 0, 0, axe_packet)
        self.script.append((self.offset, icomm_packet))
        self.offset += self.increment

    def set(self, device, table='.', **data):
        """Generate ICOMM/AXE 'set' command

        Args:
            device (str): ICOMM device name
            **data (keyword args): AXE items to set on device
            table (bytes): AXE table
        """
        axe_packet = AXE('set', data, table=table)
        icomm_packet = ICOMM('route', device, 'ground', 0, 0, axe_packet)
        self.script.append((self.offset, icomm_packet))
        self.offset += self.increment

    def statement(self, device, table='.', **data):
        """Generate ICOMM/AXE 'statement' command

        Args:
            device (str): ICOMM device name
            **data (keyword args): AXE items in statement
            table (bytes): AXE table
        """
        axe_packet = AXE('statement', data, table=table)
        icomm_packet = ICOMM('route', device, 'ground', 0, 0, axe_packet)
        self.script.append((self.offset, icomm_packet))
        self.offset += self.increment
