#!/usr/bin/env python3

import asyncio
import asyncio_dgram
import pickle
import time
import logging

from rosen.gcomm import GCOMMScript, GCOMM

logging.basicConfig(format='%(asctime)s line %(lineno)d: %(message)s')
log = logging.getLogger('rosen')

async def udp_echo_client(host, port, loop, packet_gen, ack_time=1, gcomm_log='gcomm.log'):
    """Connect to SEAQUE over UDP and start sending up GCOMM packets

    Args:
        host (str): SEAQUE address
        port (int): SEAQUE port
        loop (asyncio loop): Loop used to run this protocol
        packet_gen (generator): generator that generates gcomm packets
        ack_time (float): maximum time to receive an ACK before timeout
        gcomm_log (str): ouput log containing all sent/received GCOMM packets
    """
    # open connection
    stream = await asyncio_dgram.connect((host, port))
    # set up log
    gcomm_log_f = open(gcomm_log, 'wb')
    # get first packet to send
    packet = next(packet_gen)

    # packet = yield
    while True:
        log.debug(f"Sending {packet}")

        # wait for an ACK, and only increment packet_num counter if we receive one
        try:
            # send next packet
            await stream.send(packet.build())

            async with asyncio.timeout(ack_time):
                # wait to receive an ACK, continue receiving in the meantime
                while True:
                    data, remote_addr = await stream.recv()
                    g = GCOMM.parse(data)
                    if g.cmd == 'ok':
                        # we received the ack
                        log.debug("ACK received")
                        packet = next(packet_gen)
                        # packet = yield
                        break
                    else:
                        gcomm_log_f.write(data)
        except TimeoutError:
            # ACK has timed out
            log.error("ACK timeout")
        except ConnectionRefusedError:
            # lost UDP connection
            log.error("Lost connection")
        except StopIteration:
            # packet generator is finished.  exit loop
            break

    gcomm_log_f.close()
    stream.close()

def file_packet_generator(gcomm_script):
    """Packet generator from file

    Args:
        gcomm_script (str): path to gcomm script file
    """
    # set addr command here
    # read gcomm script file
    script = GCOMMScript.load(gcomm_script)
    for packet in script:
        yield packet

def shell_packet_generator():
    """Packet generator from user input"""
    # set addr command here
    while True:
        packet = input("Packet:").encode('utf8')
        yield packet

def run(args):
    """Run a GCOMM script file"""
    loop = asyncio.new_event_loop()
    if args.loop:
        while True:
            packet_gen = file_packet_generator(args.script)
            loop.run_until_complete(
                udp_echo_client(args.host, args.port, loop, packet_gen)
            )
    else:
        packet_gen = file_packet_generator(args.script)
        loop.run_until_complete(
            udp_echo_client(args.host, args.port, loop, packet_gen)
        )

def shell(args):
    """Run GCOMM commands interactively"""
    loop = asyncio.new_event_loop()
    packet_gen = shell_packet_generator()
    loop.run_until_complete(udp_echo_client(args.host, args.port, loop, packet_gen))
