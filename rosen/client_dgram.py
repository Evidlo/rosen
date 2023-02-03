#!/usr/bin/env python3

import asyncio
import asyncio_dgram
import pickle
import time
import logging
import argparse

logging.basicConfig(format='%(asctime)s line %(lineno)d: %(message)s')
log = logging.getLogger(__name__)
log.setLevel(logging.WARNING)

async def udp_echo_client(host, port, loop, gcomm_script, ack_time=1, gcomm_log='gcomm.log'):
    """Connect to SEAQUE over UDP and start sending up GCOMM packets

    Args:
        host (str): SEAQUE address
        port (int): SEAQUE port
        loop (asyncio loop): Loop used to run this protocol
        gcomm_script (str): path to gcomm script to run
        on_con_lost
        ack_time (float): maximum time to receive an ACK before timeout
        gcomm_log (str): ouput log containing all sent/received GCOMM packets
    """
    # open connection
    stream = await asyncio_dgram.connect((host, port))
    # read gcomm script file
    gcomm_packets = pickle.load(open(gcomm_script, 'rb'))
    # set up log
    gcomm_log_f = open(gcomm_log, 'wb')

    # loop over all packets in script file
    packet_num = 0
    while packet_num < len(gcomm_packets):
        log.debug(f"Sending packet {packet_num}/{len(gcomm_packets)}")

        # wait for an ACK, and only increment packet_num counter if we receive one
        try:
            # send next packet
            await stream.send(gcomm_packets[packet_num])

            async with asyncio.timeout(ack_time):
                # wait to receive an ACK, continue receiving in the meantime
                while True:
                    data, remote_addr = await stream.recv()
                    if data == b'ack':
                        break
                    else:
                        gcomm_log_f.write(data)
        except TimeoutError:
            log.error("ACK timeout")
        except ConnectionRefusedError:
            print("lost connection")
            log.error("Lost connection")
        else:
            # we received the ack
            log.debug("ACK received")
            packet_num += 1

    gcomm_log_f.close()
    stream.close()


def run(args):
    try:
        loop = asyncio.new_event_loop()
        if args.loop:
            while True:
                loop.run_until_complete(udp_echo_client(args.host, args.port, loop, args.script))
        else:
            loop.run_until_complete(udp_echo_client(args.host, args.port, loop, args.script))
    except KeyboardInterrupt:
        pass

def main():
    parser = argparse.ArgumentParser(description="Calculator program")
    parser._positionals.title = "commands"

    subparsers = parser.add_subparsers()
    subparsers.required = True

    # program arguments
    parser.add_argument('--debug', action='store_true', default=False, help="enable debugging")
    parser.add_argument('--host', metavar='HOST', default='127.0.0.1', type=str, help="SEAQUE host")
    parser.add_argument('--port', metavar='PORT', default=8000, type=str, help="SEAQUE port")

    # subparser for `run` command
    run_parser = subparsers.add_parser('run', help="run a GCOMM script file")
    run_parser.add_argument('--loop', action='store_true', default=False, help="loop forever")
    run_parser.add_argument('script', nargs='?', metavar='PATH', type=str, default='gcomm.script', help="script path")
    run_parser.set_defaults(func=run)

    args = parser.parse_args()

    if args.debug:
        log.setLevel(logging.DEBUG)
        log.debug("Debugging enabled")

    args.func(args)

if __name__ == '__main__':
    main()
