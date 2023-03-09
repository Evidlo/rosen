#!/usr/bin/env python3

from construct import (
    Checksum, Struct, Int8ub, Int16ub, ExprAdapter, this, Byte, GreedyBytes,
    Mapping, OffsettedEnd, Prefixed, Bytes, CString,
    VarInt, RawCopy, Probe
)
from msgpack import packb, unpackb
from pprint import pprint
import binascii

# ----- Binary Parsing/Building -----

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

class AXE:

    def __init__(self, cmd=None, data=None, table='.'):
        self.cmd, self.data, self.table = cmd, data, table

    def __repr__(self):
        if self.table == '.':
            return f"{self.cmd}({self.data})"
        else:
            return f"{self.cmd}({self.data}, table={self.table})"

    def build(self):
        return axe.build({'cmd':self.cmd, 'data':self.data, 'table':self.table})

    @classmethod
    def parse(cls, raw_bytes):
        parsed = axe.parse(raw_bytes)
        return cls(parsed.cmd, parsed.data, parsed.table)

