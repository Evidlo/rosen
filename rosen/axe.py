#!/usr/bin/env python3

from construct import (
    Checksum, Struct, Int8ub, Int16ub, ExprAdapter, this, Byte, GreedyBytes,
    Mapping, OffsettedEnd, Prefixed, Bytes, CString,
    VarInt, RawCopy, Probe
)
from msgpack import packb, unpackb
import binascii

axe = Struct(
    "cmd" / Mapping(
        Byte,
        # command map
        {
            'execute': ord('!'),
            'query': ord('?'),
            'set': ord('>'),
            'statement': ord('.')
        }
    ),
    "table" / CString('ascii'),
    # msgpack pack/unpack data
    "data" / ExprAdapter(GreedyBytes, lambda b, _: unpackb(b), lambda b, _: packb(b))
)

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
        "from" / device_map,
        "payload" / OffsettedEnd(-4, GreedyBytes),
    )),
    "checksum" / Checksum(
        Bytes(4),
        lambda data: binascii.crc32(data).to_bytes(4, 'big'),
        this.body.data
    )
))

class AXEScript:

    def __init__(self, offset=0, increment=1):
        """Class for generating AXE command sequences

        Args:
            offset (float): time offset of next command generated
            increment (float): seconds to increment offset after new command
        """
        # current time offset
        self.offset = offset
        # offset time increment after adding a command
        self.increment = increment
        # list of tuples containing (execution_time, icomm_packet)
        self.script = []

    def execute(self, device, command, table='.'):
        """Generate ICOMM/AXE 'execute' command

        Args:
            device (str): ICOMM device name
            command (str): AXE command to run on device
            table (bytes): AXE table
        """
        assert type(command) is str, "command argument must be string"
        axe_bytes = axe.build({'cmd':'execute', 'table':table, 'data':command})
        icomm_bytes = icomm.build({'body':{'value':
            {'cmd':'route', 'to':device, 'from':'eduplsb', 'payload':axe_bytes}
        }})
        self.script.append((self.offset, icomm_bytes))
        self.offset += self.increment

    def query(self, device, items, table='.'):
        """Generate ICOMM/AXE 'query' command

        Args:
            device (str): ICOMM device name
            items (list): AXE items to query on device
            table (bytes): AXE table
        """
        assert type(items) is list, "items argument must be list"
        axe_bytes = axe.build({'cmd':'query', 'table':table, 'data':items})
        icomm_bytes = icomm.build({'body':{'value':
            {'cmd':'route', 'to':device, 'from':'eduplsb', 'payload':axe_bytes}
        }})
        self.script.append((self.offset, icomm_bytes))
        self.offset += self.increment

    def set(self, device, table='.', **data):
        """Generate ICOMM/AXE 'set' command

        Args:
            device (str): ICOMM device name
            **data (keyword args): AXE items to set on device
            table (bytes): AXE table
        """
        axe_bytes = axe.build({'cmd':'set', 'table':table, 'data':data})
        icomm_bytes = icomm.build({'body':{'value':
            {'cmd':'route', 'to':device, 'from':'ground', 'payload':axe_bytes}
        }})
        self.script.append((self.offset, icomm_bytes))
        self.offset += self.increment

    def statement(self, device, table='.', **data):
        """Generate ICOMM/AXE 'statement' command

        Args:
            device (str): ICOMM device name
            **data (keyword args): AXE items in statement
            table (bytes): AXE table
        """
        axe_bytes = axe.build({'cmd':'statement', 'table':table, 'data':data})
        icomm_bytes = icomm.build({'body':{'value':
            {'cmd':'route', 'to':device, 'from':'ground', 'payload':axe_bytes}
        }})
        self.script.append((self.offset, icomm_bytes))
        self.offset += self.increment
