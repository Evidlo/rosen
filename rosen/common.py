#!/usr/bin/env python3
from datetime import datetime, timezone
from dateutil.parser import parse
from dataclasses import fields

def handle_time(t):
    """Coerce all sorts of times to Unix time

    Args:
        t (str, int, or datetime.datetime): Datetime of some type.
            TZ is assumed to be UTC if not given

    Return:
    """
    if type(t) is str:
        d = parse(t)
    elif type(t) is int:
        return t
    else:
        d = t

    # replace timezone if not specified
    d = d.replace(tzinfo=d.tzinfo or timezone.utc)

    return int(d.timestamp())

class Packet:

    def __repr__(self):
        """String representation of Packet"""

        # only show fields changed from default
        display_fields = []
        for field in fields(self):
            val = getattr(self, field.name)
            if field.name == 'cmd':
                display_fields.append(self.cmd)
            elif field.name in ('n', 'm') and self.m > 0:
                display_fields.append(f"{field.name}={val}")
            elif val != field.default:
                display_fields.append(f"{field.name}={val}")

        return f"{type(self).__name__}({', '.join(display_fields)})"


class Script:

    def __iter__(self):
        """Allow iterating over packet objects within script"""
        for g in self.script:
            yield g

    def __len__(self):
        return len(self.script)


class MutInt(int):
    """Behaves exactly like an int except is mutable and passed by reference"""

    def __init__(self, value):
        self.value = value

    def __add__(self, other):
        self.value += other
        return self

    def __sub__(self, other):
        self.value -= other
        return self

    def __mul__(self, other):
        self.value *= other
        return self

    def __div__(self, other):
        self.value /= other
        return self

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.value == other

    def __gt__(self, other):
        return self.value > other

    def __lt__(self, other):
        return self.value < other

    def __geq__(self, other):
        return self.value >= other

    def __leq__(self, other):
        return self.value <= other
