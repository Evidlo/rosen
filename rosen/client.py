#!/usr/bin/env python3

import asyncio
import logging
from pathlib import Path
import sys

from rosen.gcomm import GCOMMScript, GCOMM
from rosen.icomm import ICOMMScript, ICOMM
from rosen.axe import AXE

logging.basicConfig(format='%(message)s')
log = logging.getLogger('rosen')

class RADCOM:
    """Class for holding state communicating with RADCOM

    Args:
        host (str): RADCOM address
        port (int): RADCOM port

    Attributes:
        ok_received (asyncio.Event): whether an OK has been received for the last
            message sent
        host (str): RADCOM address
        port (int): RADCOM port
        should_quit (bool): set this to True to tell infinite-running `receive`
            coroutine to quit

    """
    def __init__(self, host, port):
        self.host, self.port = host, port
        self.ok_received = None
        self.should_quit = False

    async def connect(self):
        """Open connection to RADCOM"""
        try:
            self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        except ConnectionRefusedError:
            log.error("Connection refused")
            sys.exit(1)

    async def close(self):
        """Clean up connection"""
        self.writer.close()
        await writer.wait_closed()

    async def receive(self):
        """Forever-running coroutine that logs/prints received packets and checks for OK"""
        if self.ok_received is None:
            self.ok_received = asyncio.Event()
        while not self.should_quit:
            data = await self.reader.readexactly(GCOMM.size)
            try:
                packet = GCOMM.parse(data)
                print(f"Received {packet}")
                if packet.cmd == 'ok':
                    self.ok_received.set()

            except:
                print('Bad Packet')
            
    async def wait_ok(self, timeout=100):
        """Coroutine which waits for an OK to come through, or times out

        Args:
            timeout (float): max time to wait for an OK

        Returns:
            bool: whether an OK was received within the timeout period
        """
        if self.ok_received is None:
            self.ok_received = asyncio.Event()
        try:
            await asyncio.wait_for(self.ok_received.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            log.error("OK timed out")
            return False
        return True

    async def send(self, packet):
        """Send a packet to GCOMM

        Args:
            packet (GCOMM): GCOMM packet to send
        """
        print(f"Sending {packet}")
        self.writer.write(packet.build())
        await self.writer.drain()
        # waiting for an OK
        if self.ok_received is None:
            self.ok_received = asyncio.Event()
        self.ok_received.clear()

# ----- Interactive Shell -----

async def shell_client(r, helper, loop):
    """
    Shell coroutine

    Args:
        r (RADCOM): RADCOM state object
        helper (str): path to Python script containing user defined functions/variables
        loop (asyncio loop): kill the asyncio loop when the shell completes
    """

    from ptpython.repl import embed
    from prompt_toolkit.enums import EditingMode

    await r.connect()
    # kick off receive coroutine
    receiving = asyncio.create_task(r.receive())

    def send(command):
        asyncio.create_task(r.send(command))

    if helper is not None:
        exec(Path(helper).read_text())

    def repl_config(repl):
        repl.show_status_bar = False
        repl.confirm_exit = False
        repl.editing_mode = EditingMode.VI

    print('Use send() to stick things in the queue')
    print('CTRL+D to quit the shell')
    await embed(
        globals=globals(),
        locals=locals(),
        return_asyncio_coroutine=True,
        patch_stdout=True,
        configure=repl_config
    )

    # tell coroutines to exit, and wait for exit
    # r.should_quit = True
    # await receiving
    # FIXME: r.should_quit doesn't work
    loop.stop()

def shell(args):
    """Argparse entry point for `shell` command"""
    r = RADCOM(args.host, args.port)
    loop = asyncio.get_event_loop()
    asyncio.run(shell_client(r, args.script, loop))

# ----- Manual Script Running -----

async def run_client(r, script_file, loop):
    """
    Script runner coroutine

    Args:
        r (RADCOM): RADCOM state object
        script (str or GCOMMScript): GCOMM script to execute
        loop (asyncio loop): kill the asyncio loop when the shell completes
    """
    await r.connect()
    # kick off receive coroutine
    receiving = asyncio.create_task(r.receive())

    if type(script_file) is str:
        script = GCOMMScript.load(script_file)
    elif type(script) is GCOMMScript:
        script = script_file
    else:
        raise TypeError("Invalid type for script_file")

    for packet in script:
        # wait for an OK, resend previous packet if no OK received
        await r.send(packet)
        while not await r.wait_ok():
            await r.send(packet)

    # tell coroutines to exit, and wait for exit
    # r.should_quit = True
    # await receiving
    # FIXME: r.should_quit doesn't work
    loop.stop()


def run(args):
    """Argparse entry point for `run` command"""
    r = RADCOM(args.host, args.port)
    # FIXME: ugly
    loop = asyncio.get_event_loop()
    asyncio.run(run_client(r, args.script, loop))
