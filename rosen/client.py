#!/usr/bin/env python3

import asyncio
import pickle
import time
import logging
from pathlib import Path

from rosen.gcomm import GCOMMScript, GCOMM
from rosen.icomm import ICOMMScript, ICOMM
from rosen.axe import AXE

logging.basicConfig(format='%(message)s')
log = logging.getLogger('rosen')


# FIXME: python3.7 - this can be simplified if we drop 3.7
# python3.7 doesn't have anext.  copy it from
# https://github.com/python/cpython/pull/8895/files#diff-2ea92c5fc4c308512ab17f95ccd627a366fbe9d83a618e4f87c1de494117e406R442-R458
async def anext(async_iterator):
    """Return the next item from the async iterator.
    """
    from collections.abc import AsyncIterator
    if not isinstance(async_iterator, AsyncIterator):
        raise TypeError(f'anext expected an AsyncIterator, got {type(async_iterator)}')
    anxt = type(async_iterator).__anext__
    return await anxt(async_iterator)

# FIXME: python3.7 - this can be simplified if we drop 3.7
# python3.7 asyncio doesn't support timeout context manager.  use asyncio.wait_for() instead
async def wait_for_ok(reader, gcomm_log_f):
    """Loop forever until we receive an OK.  Write received messages to log in meantime"""
    while True:
        data = await reader.readexactly(GCOMM.size)
        g = GCOMM.parse(data)
        print(f"Received {g}")
        if g.cmd == 'ok':
            # we received the ack
            print("ACK received")
            return
        else:
            gcomm_log_f.write(data)


async def client(host, port, packet_gen, ack_time=2, gcomm_log='gcomm.log'):
    """Connect to SEAQUE over UDP and start sending up GCOMM packets

    Args:
        host (str): SEAQUE address
        port (int): SEAQUE port
        packet_gen (generator): generator that generates gcomm packets
        ack_time (float): maximum time to receive an ACK before timeout
        gcomm_log (str): ouput log containing all sent/received GCOMM packets
    """
    # open connection
    try:
        reader, writer = await asyncio.open_connection(host, port)
        print("Connected")
    except ConnectionRefusedError:
        log.error("Connection refused")
        await asyncio.sleep(1)
        return
    # set up log
    gcomm_log_f = open(gcomm_log, 'wb')
    # get first packet to send
    packet = await anext(packet_gen)

    # packet = yield
    while True:
        log.debug(f"Sending {packet}")

        try:
            # send next packet
            writer.write(packet.build())
            await writer.drain()

            # FIXME: python3.7 - this can be simplified if we drop 3.7
            # wait to receive an ACK, continue receiving in the meantime
            await asyncio.wait_for(wait_for_ok(reader, gcomm_log_f), timeout=ack_time)

            packet = await anext(packet_gen)

        except asyncio.TimeoutError:
            # ACK has timed out
            log.error("Didn't receive OK from RADCOM")
            break
        except ConnectionResetError:
            # lost UDP connection
            log.error("Lost connection")
            await asyncio.sleep(1)
            break
        except (StopAsyncIteration, StopIteration):
            # packet generator is finished.  exit loop
            log.debug("Packet generator StopIteration")
            break
        except asyncio.exceptions.IncompleteReadError:
            print("EOF before complete GCOMM packet")
            break
        except AttributeError:
            log.error("Cannot send packet.  Not a GCOMM packet")
            # packet = await anext(packet_gen)
            packet = await type(packet_gen).__anext__(packet_gen)

    gcomm_log_f.close()
    writer.close()
    await writer.wait_closed()

# ----- Manual Script Running -----

async def file_packet_generator(gcomm_script):
    """Packet generator from file or GCOMMScript
    Args:
        gcomm_script (str or GCOMMScript): path to gcomm script file or GCOMMScript object
    """
    # set addr command here
    # read gcomm script file
    if type(gcomm_script) is str:
        script = GCOMMScript.load(gcomm_script)
    else:
        script = gcomm_script
    for packet in script:
        yield packet

def run(args):
    """Run a GCOMM script file"""
    loop = asyncio.get_event_loop()
    if args.loop:
        while True:
            packet_gen = file_packet_generator(args.script)
            loop.run_until_complete(
                client(args.host, args.port, packet_gen)
            )
    else:
        packet_gen = file_packet_generator(args.script)
        loop.run_until_complete(
            client(args.host, args.port, packet_gen)
        )

# ----- Interactive Shell -----

async def interactive_shell(q, script, loop, args, packet_gen):
    """
    Shell coroutine which has access to the queue

    Args:
        q (Queue): queue for sending data to packet generator
        script (str): path to Python script containing user
            defined variables
        loop (asyncio loop): kill the asyncio loop when the shell completes
    """

    from ptpython.repl import embed
    from prompt_toolkit.enums import EditingMode

    def repl_config(repl):
        repl.show_status_bar = False
        repl.confirm_exit = False
        repl.editing_mode = EditingMode.VI

    def send(msg):
        q.put_nowait(msg)

    if script is not None:
        exec(Path(script).read_text())

    print('Use send() to stick things in the queue')
    print('CTRL+D to quit the shell')
    await embed(
        globals=globals(),
        locals=locals(),
        return_asyncio_coroutine=True,
        patch_stdout=True,
        configure=repl_config
    )
    loop.stop()


async def shell_packet_generator(q):
    """Packet generator from user input

    Args:
        q (Queue): queue for receiving data from shell
    """
    # set addr command here
    while True:
        yield await q.get()

def shell(args):
    """Run GCOMM commands interactively"""

    loop = asyncio.get_event_loop()
    q = asyncio.Queue()
    packet_gen = shell_packet_generator(q)
    # loop.run_until_complete(client(args.host, args.port, packet_gen))
    asyncio.ensure_future(client(args.host, args.port, packet_gen))

    loop.run_forever()
