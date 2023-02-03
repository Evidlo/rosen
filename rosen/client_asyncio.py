#!/usr/bin/env python3

import asyncio
import pickle


class GCOMMProtocol:
    # def __init__(self, loop, gcomm_script, on_con_lost, ack_time=1, gcomm_log='gcomm.log'):
    def __init__(self, loop, gcomm_script, ack_time=1, gcomm_log='gcomm.log'):
        """Connect to SEAQUE over UDP and start sending up GCOMM packets

        Args:
            loop (asyncio loop): Loop used to run this protocol
            gcomm_script (str): path to gcomm script to run
            on_con_lost
            ack_time (float): maximum time to receive an ACK before timeout
            gcomm_log (str): ouput log containing all sent/received GCOMM packets
        """
        self.loop = loop
        self.gcomm_log = gcomm_log
        # self.on_con_lost = on_con_lost
        self.transport = None
        self.ack_time = ack_time
        self.ack_timer = None
        self.gcomm_packets = pickle.load(open(gcomm_script, 'rb'))
        self.packet_num = 0


    # --- Asyncio UDP Callbacks ---

    def connection_made(self, transport):
        "Begin sending GCOMM script.  Open socket and send first command"
        self.transport = transport
        print('first send')
        self.send_packet()

    def datagram_received(self, data, addr):
        """Called when GCOMM packet received"""
        self.log_packet(data)

        if data == b'ack':
            self.ack_received()
            self.send_packet()

    # --- Packet handling ---

    def send_packet(self, repeat=False):
        """Generator to send next packet in the GCOMM script

        Args:
            repeat (bool): repeat the last sent packet
        """
        if repeat == False:
            self.packet_num += 1

        if self.packet_num < len(self.gcomm_packets):
            self.transport.sendto(self.gcomm_packets[self.packet_num])
            self.wait_ack()
        else:
            self.transport.close()


    def log_packet(self, data):
        with open(self.gcomm_log, 'ab') as f:
            f.write(data)

    # --- ACKING ---

    def wait_ack(self):
        """Wait for a GCOMM ACK packet"""
        self.ack_timer = self.loop.call_later(self.ack_time, self.timeout_ack)

    def ack_received(self):
        """Called when GCOMM ACK packet received"""
        print('ack received')
        if self.ack_timer is not None:
            self.ack_timer.cancel()

    def timeout_ack(self):
        """Called when an ACK times out"""
        print("ack timeout.  resending")
        self.send_packet(repeat=True)

    def error_received(self, exc):
        print('Error received:', exc)

    def connection_lost(self, exc):
        print("Connection closed")
        # FIXME ?
        self.on_con_lost.set_result(True)


async def run():
    # Get a reference to the event loop as we plan to use
    # low-level APIs.
    loop = asyncio.get_running_loop()

    # on_con_lost = loop.create_future()

    transport, protocol = await loop.create_datagram_endpoint(
        # lambda: GCOMMProtocol(loop, 'gcomm.script', on_con_lost),
        lambda: GCOMMProtocol(loop, 'gcomm.script'),
        remote_addr=('127.0.0.1', 9999))
    loop.run_until_complete()

    try:
        await on_con_lost
    finally:
        transport.close()

def main():
    try:
        asyncio.run(run())
        print('first one stopped, starting next- ------------------------------------')
        asyncio.run(run())
        print('second one stopped ------------------------------------')
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()
