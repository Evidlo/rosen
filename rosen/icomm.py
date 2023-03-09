#!/usr/bin/env python3

from construct import (
    Checksum, Struct, Int8ub, Int16ub, ExprAdapter, this, Byte, GreedyBytes,
    Mapping, OffsettedEnd, Prefixed, Bytes, CString,
    VarInt, RawCopy, Probe
)
from msgpack import packb, unpackb
from pprint import pprint
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

icomm = Prefixed(Int16ub, Struct(
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
        "payload" / OffsettedEnd(-4, GreedyBytes),
    )),
    "checksum" / Checksum(
        Bytes(4),
        lambda data: binascii.crc32(data).to_bytes(4, 'big'),
        this.body.data
    )
))

class ICOMM:
    """Class for building/parsing ICOMM packet"""

    def __init__(self, cmd=None, to=None, frm='', payload=None):
        self.cmd, self.to, self.frm, self.payload = cmd, to, frm, payload

    def __repr__(self):
        """ICOMM string represenetation"""
        if self.cmd == 'ack':
            return f"{self.frm}→{self.to}: ACK"
        elif self.cmd == 'nack':
            return f"{self.frm}→{self.to}: NACK"
        else:
            return f"{self.frm}→{self.to}: {self.payload}"


    def build(self):
        """Build bytes for GCOMM packet

        Returns:
            bytes
        """
        axe_bytes = self.payload.build()
        return icomm.build({'body':{'value':
            {'cmd':self.cmd, 'to':self.to, 'frm':self.frm, 'payload':axe_bytes}
        }})

    @classmethod
    def parse(cls, raw_bytes):
        parsed = icomm.parse(raw_bytes)
        return cls(
            parsed.body.value.cmd, parsed.body.value.to, parsed.body.value.frm,
            parsed.body.value.payload
        )


# ----- Scripting -----

class ICOMMScript:

    def __init__(self, offset=0, increment=1):
        """Class for generating ICOMM script sequences

        Args:
            offset (float): time offset of next ICOMM packet
            increment (float): seconds to increment offset after new command
        """
        # current time offset
        self.offset = offset
        # offset time increment after adding a command
        self.increment = increment
        # list of tuples containing (execution_time, icomm_packet)
        self.script = []

    def __len__(self):
        return len(self.script)

    def __repr__(self):
        s = "ICOMMScript"
        s += f"\n    {'Time Offset':<15}{'From':<15}{'To':<15}"
        s += f"\n    {'-----------':<15}{'----':<15}"
        for cmd in self.script:
            s += f"\n    {cmd[0]:<20}{str(cmd[1].frm):<20}"

        return s

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
        icomm_packet = ICOMM('route', device, 'ground', axe_packet)
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
        icomm_packet = ICOMM('route', device, 'ground', axe_packet)
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
        icomm_packet = ICOMM('route', device, 'ground', axe_packet)
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
        icomm_packet = ICOMM('route', device, 'ground', axe_packet)
        self.script.append((self.offset, icomm_packet))
        self.offset += self.increment
