#!/usr/bin/env python3

from construct import Struct, ExprAdapter, Byte, GreedyBytes, Mapping, CString, If, Int16ub, this
from msgpack import packb, unpackb
from rich.console import Console
from rich.syntax import Syntax
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
    "tx_id" / If(this.cmd == 'query' or this.cmd == 'statement', Int16ub),
    # msgpack pack/unpack data
    "data" / ExprAdapter(GreedyBytes, lambda b, _: unpackb(b), lambda b, _: packb(b, use_single_float=True))
)

class AXE:

    def __init__(self, cmd=None, data=None, tx_id=0):
        self.cmd, self.data, self.tx_id = cmd, data, tx_id

    def __repr__(self):
        s = f"{self.cmd}({self.data})"
        return s

    def build(self):
        return axe.build({'cmd':self.cmd, 'tx_id':self.tx_id, 'data':self.data})

    @classmethod
    def parse(cls, raw_bytes):
        parsed = axe.parse(raw_bytes)
        return cls(parsed.cmd, parsed.data)

