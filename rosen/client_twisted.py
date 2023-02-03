from common import port
from twisted.internet import protocol, task
import pickle

class GCOMMProtocol(protocol.DatagramProtocol):
    def __init__(self, host, port, reactor, gcomm_script, gcomm_log='gcomm.log'):
        """Connect to SEAQUE over UDP and start sending up GCOMM packets

        Args:
            host (str): SEAQUE hostname
            port (str): SEAQUE UDP port
            reactor (twisted.internet.reactor): Reactor used to run this protocol
            gcomm_script (str): path to gcomm script to run
            gcomm_log (str): ouput log containing all sent/received GCOMM packets
        """
        self.host = host
        self.port = port
        self.reactor = reactor
        self.ack_timeout = None
        self.gcomm_log = gcomm_log
        self.script_sender = self.packetSender(gcomm_script)

    def startProtocol(self):
        "Begin sending GCOMM script.  Open socket and send first command"
        self.transport.connect(self.host, self.port)
        next(self.script_sender)

    def stopProtocol(self):
        "Called when GCOMM script upload finished.  Clean up socket"
        self.reactor.listenUDP(0, self)

    def packetSender(self, gcomm_script):
        """Generator to send next packet in the GCOMM script"""
        gcomm_packets = pickle.load(open(gcomm_script, 'rb'))

        for packet in gcomm_packets:
            self.sendDatagram(packet)
            yield

        self.stopProtocol()

    def sendDatagram(self, datagram):
        "Send a GCOMM packet"
        try:
            self.transport.write(datagram, (self.host, self.port))
            print(f"sent {datagram}")
        except:
            pass

    def datagramReceived(self, datagram, host):
        """Called when GCOMM packet received"""
        self.logPacket(datagram)
        if datagram == 'ack' or True:
            self.receiveACK()
            next(self.script_sender)

    def logPacket(self, datagram):
        with open(self.gcomm_log, 'ab') as f:
            f.write(datagram)

    # --- ACKING ---

    def sendACK(self):
        """Send a GCOMM ACK packet"""
        self.ack_timeout = self.reactor.callLater(self.timeoutACK)

    def receiveACK(self):
        """Called when GCOMM ACK packet received"""
        print('we got ACK!')
        if self.ack_timeout is not None:
            self.ack_timeout.cancel()

    def timeoutACK(self):
        """Called when an ACK times out"""

def main():
    test()
    print('first one stopped, starting next- ------------------------------------')
    test()
    print('second one stopped ------------------------------------')

def test():
    from twisted.internet import reactor
    protocol = GCOMMProtocol('127.0.0.1', port, reactor, 'gcomm.script')
    t = reactor.listenUDP(0, protocol)
    reactor.run()
    reactor.crash()

if __name__ == '__main__':
    main()
