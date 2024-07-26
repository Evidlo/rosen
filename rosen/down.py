import socket
import time
import threading
import pickle as pkl

from rosen.gcomm import GCOMM

sock = None
packets = []

def download():

    global sock
    global n
    global m
    global recv_l
    global packets

    data = b''

    while True:
        d = sock.recv(4162)
        data = b''.join([data, d])
        recv_l = recv_l + len(d)
        if (len(data) >= 4162):
            packet = GCOMM.parse(data[:4162])
            data = data[4162:]
            if packet.cmd == 'app_file':
                n = packet.n
                m = packet.m
            packets.append(packet)


def down_file(args):

    global sock
    global m
    global n
    global recv_l
    global packets

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_QUICKACK, 1)

    sock.connect((args.host, args.port))

    n = 0
    m = 1
    recv_l = 0

    # Get size of file
    packets = []
    sock.send(GCOMM('file_sd', filename=args.downfile).build())
    datav = []
    sock.settimeout(3)
    while True:
        try:
            datav.append(sock.recv(4162))
        except socket.timeout:
            break

    sock.settimeout(None)
    fullsize = 0
    for d in datav:
        p = GCOMM.parse(d)
        print(p)
        if p.m > fullsize:
            fullsize = p.m

    start_t = time.time()
    sock.send(GCOMM('disable_sd').build())
    time.sleep(0.2)
    sock.send(GCOMM('down_file', filename=args.downfile).build())


    down_thread = threading.Thread(target=download, daemon=True)
    down_thread.start()

    print()
    while n != m:
        print(f'\rGot {n} of {m} packets at {n / (time.time() - start_t):.3f} packets/s', end='')
        #print(f'\rGot {recv_l} of {fullsize} bytes ', end='')
        time.sleep(0.25)

    print(f'\rGot {n} of {m} packets at {n / (time.time() - start_t):.3f} packets/s')

    with open(str(int(time.time())) + '-' + args.downfile.replace('.','_') + '.pkl', 'wb') as f:
        pkl.dump(packets, f)

    # Read packets for errors here
    error_val_max = 0
    for p in packets:
        try:
            error_val = p.packet.payload.data['error_reg']
            if error_val > error_val_max:
                error_val_max = error_val
        except:
            pass

    if error_val_max >= 200 and error_val_max < 300:
        print(f'Non-critical error {error_val_max} reported by payload, alert SEAQUE team.')
    elif error_val_max > 300:
        print(f'Critical error {error_val_max} reported by payload, alert SEAQUE team. DO NOT proceed with upload.')

    exit()

