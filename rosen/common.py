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
        """String representation of GCOMM"""

        # only show fields changed from default
        display_fields = [self.cmd]
        for field in fields(self):
            if field.name == 'cmd':
                continue
            val = getattr(self, field.name)
            if val != field.default:
                display_fields.append(f"{field.name}={val}")

        return f"{type(self).__name__}({', '.join(display_fields)})"


class Script:

    def __iter__(self):
        """Allow iterating over packet objects within script"""
        for g in self.script:
            yield g

    def __len__(self):
        return len(self.script)
