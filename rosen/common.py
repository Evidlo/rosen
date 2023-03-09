#!/usr/bin/env python3
from datetime import datetime, timezone
from dateutil.parser import parse

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
