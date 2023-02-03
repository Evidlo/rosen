from construct import Bytes, PaddedString, Struct, Int32ub, ExprAdapter

def bytes2ip(b, *args):
    return '.'.join(map(str, b))
def ip2bytes(ip, *args):
    return bytes(map(int, ip.split('.')))

# ----- Command definitions -----

gcomm = Struct(
    "cmd" / Enum(
        Byte,
        exec_now=1,
        abort_script=2,
        app_file=3,
        rm_file=4,
        exec_file=5,
        down_file=6,
        list_file=7,
        clear_sd=8,
        down_ok=9,
        down_nok=10,
        set_addr=11,
        get_time=12,
        set_time=13,
        reset_radcom=14,
        ok=15,
        nok=16
    ),
    "filename" / Default(PaddedString(16, 'ascii'), ''),
    "n" / Default(Int32ub, 0),
    "m" / Default(Int32ub, 0),
    "offset" / Default(Int32ub, 0),
    "addr" / Default(ExprAdapter(Bytes(4), bytes2ip, ip2bytes), '0.0.0.0'),
    "time" / Default(Int32ub, 0),
    "err" / Default(PaddedString(64, 'ascii'), ''),
    "script" / Default(GreedyBytes, b'')
)
