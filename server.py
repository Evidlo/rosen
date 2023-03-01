from twisted.internet import reactor
from twisted.internet.protocol import DatagramProtocol
import time


class Echo(DatagramProtocol):
    def datagramReceived(self, data, addr):
        time.sleep(.3)
        print(f"received {data!r} from {addr}")
        if True or data != b'\x08':
            self.transport.write(b'ack', addr)
            self.transport.write(b'result', addr)


reactor.listenUDP(8000, Echo())
reactor.run()
