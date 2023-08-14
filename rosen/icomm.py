#!/usr/bin/env python3

from construct import (
    Checksum, Struct, Int8ub, Int16ub, ExprAdapter, this, Byte, GreedyBytes,
    Mapping, Prefixed, Bytes, CString,
    VarInt, RawCopy, Probe, Padded
)
from dataclasses import dataclass
from msgpack import packb, unpackb
from rich.console import Console
from rich.table import Table
import binascii
from typing import Union

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
command_map = Mapping(
    Byte,
    # command map
    {
        'cmd': 0,
        'ack': 1,
        'nack': 2,
        'busy': 3
    }
)

icomm_construct = Padded(
    4092,
    Struct(
        "body" / RawCopy(Struct(
            "size" / Int16ub,
            "cmd" / command_map,
            "to" / device_map,
            "frm" / device_map,
            "last" / device_map,
            "seq" / Int8ub,
            "n" / Int8ub,
            "m" / Int8ub,
            "payload" / Bytes(this.size),
        )),
        "checksum" / Checksum(
            Bytes(4),
            lambda data: binascii.crc32(data).to_bytes(4, 'big'),
            this.body.data
        )
    )
)

@dataclass(repr=False)
class ICOMM(Packet):
    """Class for building/parsing ICOMM packet"""
    cmd: str
    to: str
    payload: AXE
    frm: str = 'ground'
    n: int = 0
    m: Union[int, MutInt] = 0

    size = icomm_construct.sizeof()

    def build(self):
        """Build bytes for GCOMM packet

        Returns:
            bytes
        """
        axe_bytes = self.payload.build()
        return icomm_construct.build({'body':{'value':
            {
                'size': len(axe_bytes), 'cmd':self.cmd, 'to':self.to, 'frm':self.frm,
                'last':self.frm, 'seq':0, 'n':self.n, 'm':self.m, 'payload':axe_bytes
            }
        }})

    @classmethod
    def parse(cls, raw_bytes):
        parsed = icomm_construct.parse(raw_bytes)
        return cls(
            parsed.body.value.cmd, parsed.body.value.to,
            AXE.parse(parsed.body.value.payload), parsed.body.value.frm,
            parsed.body.value.n, parsed.body.value.m,
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
        # offset time increment after adding a command
        self.increment = increment
        # list of tuples containing (execution_time, icomm_packet)
        self.script = []

    def __repr__(self):
        """Pretty print object as table"""

        table = Table(
            "Offset", "From", "To", "Payload",
            title=f"ICOMMScript: {self.name}",
        )

        for cmd in self.script:
            table.add_row(
                str(cmd[0]), cmd[1].frm, cmd[1].to,
                str(cmd[1].payload)
            )

        console = Console()
        with console.capture() as capture:
            console.print(table)

        return capture.get()

    # ----- AXE Helper Functions -----
    # Helper functions for quickly building ICOMM/AXE commands

    def execute(self, device, command):
        """Generate ICOMM/AXE 'execute' command

        Args:
            device (str): ICOMM device name
            command (str): AXE command to run on device
        """
        axe_packet = AXE('execute', command)
        icomm_packet = ICOMM('cmd', device, axe_packet)
        self.script.append((self.offset, icomm_packet))
        self.offset += self.increment

    def query(self, device, items):
        """Generate ICOMM/AXE 'query' command

        Args:
            device (str): ICOMM device name
            items (list): AXE items to query on device
        """
        axe_packet = AXE('query', items)
        icomm_packet = ICOMM('cmd', device, axe_packet)
        self.script.append((self.offset, icomm_packet))
        self.offset += self.increment

    def set(self, device, **data):
        """Generate ICOMM/AXE 'set' command

        Args:
            device (str): ICOMM device name
            **data (keyword args): AXE items to set on device
        """
        axe_packet = AXE('set', data)
        icomm_packet = ICOMM('cmd', device, axe_packet)
        self.script.append((self.offset, icomm_packet))
        self.offset += self.increment

    def statement(self, device, **data):
        """Generate ICOMM/AXE 'statement' command

        Args:
            device (str): ICOMM device name
            **data (keyword args): AXE items in statement
        """
        axe_packet = AXE('statement', data)
        icomm_packet = ICOMM('cmd', device, axe_packet)
        self.script.append((self.offset, icomm_packet))
        self.offset += self.increment
