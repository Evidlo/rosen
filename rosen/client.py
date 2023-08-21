#!/usr/bin/env python3

import asyncio
import pickle
import time
import logging

from rosen.gcomm import GCOMMScript, GCOMM

logging.basicConfig(format='%(asctime)s line %(lineno)d: %(message)s')
log = logging.getLogger('rosen')

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
    except ConnectionRefusedError:
        log.error("Connection refused")
        await asyncio.sleep(1)
        return
    # set up log
    gcomm_log_f = open(gcomm_log, 'wb')
    # get first packet to send
    packet = next(packet_gen)

    # packet = yield
    while True:
        log.debug(f"Sending {packet}")

        try:
            # send next packet
            writer.write(packet.build())
            await writer.drain()

            async with asyncio.timeout(ack_time):
                # wait to receive an ACK, continue receiving in the meantime
                while True:
                    data = await reader.readexactly(GCOMM.size)
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
            break
        except ConnectionResetError:
            # lost UDP connection
            log.error("Lost connection")
            await asyncio.sleep(1)
            break
        except StopIteration:
            # packet generator is finished.  exit loop
            log.error("Packet generator StopIteration")
            break
        except asyncio.exceptions.IncompleteReadError:
            print("EOF before complete GCOMM packet")
            break

    gcomm_log_f.close()
    writer.close()
    await writer.wait_closed()

def file_packet_generator(gcomm_script):
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

# def shell_packet_generator():
#     """Packet generator from user input"""
#     # set addr command here
#     while True:
#         packet = input("Packet:").encode('utf8')
#         yield packet

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

# def shell(args):
#     """Run GCOMM commands interactively"""
#     loop = asyncio.new_event_loop()
#     packet_gen = shell_packet_generator()
#     loop.run_until_complete(udp_echo_client(args.host, args.port, loop, packet_gen))
