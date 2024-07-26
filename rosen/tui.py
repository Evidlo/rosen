import threading
import socket
import sys
import pickle as pkl
import time

from rosen.gcomm import GCOMM

from rosen.term import Console
import rosen.shell_parse

if len(sys.argv) > 1:
    pkl_fname = sys.argv[1]
else:
    pkl_fname = 'NA'

asciiart = '''                                                        KN                                          
                                                        NM                                          
                                                    ,okKMMKOd;                                      
                                                  oNXl,.  .'c0Wd.                                   
                                                .XW:          ,NN.                                  
   .;ccc;.       ,;;;;;;;;;;;.         ;.       kM:  .;cllc;.  .MK  .;.          ;,    .;;;;;;;;;;;,
 lNXdc:lxXNx     NMdddddddddd.        0MW.      KM;dNXxlc:lxKWx'MW  :Md          MN    :MKdddddddddl
;MX       .;     NM                  xM:XW.     cc,O.        .kc,d  :Md          MN    :Md          
.NWo'.           NM                 oMl .WX     lc;0'        .Oc;d  :Md          MN    :Md          
  'lkXNKko;      NMNNNNNNNN'       lMx   'W0    KM,oXNkolcoxXNd.MW  :Md          MN    :MWNNNNNNNK  
       .'c0Wo    NM               ;MO     ;Mk   kM:  .,:cc:,.  'MK  :Mx         .MN    :Md          
 .         WM    NM              'WMNXXXXXXWMx  .XWc          ;WN.  .WN.        oMx    :Md          
oM0l'.  .:KWc    NM..........   .WX.        xMo   lNXo,....,oXNo     .KWo'   .;OMx     :Mk..........
 .:d0KXK0x:      kOOOOOOOOOOO;  xO.          xO.    'lx0MM0ko,         'lOKXX0x:.      'OOOOOOOOOOOO
                                                        NM                                          
                                                        KN                                          '''

connection_started = False
sock = None

def parse(string):
    'Parses Commands'

    while not connection_started:
        time.sleep(1)

    parsed = rosen.shell_parse.cmd_parse(string)
    if type(parsed) == GCOMM:
        dp = parsed.build()
        d = b''.join([b'\0\0', dp])
        sock.send(dp)



def get_packets(packets):

    'Continuous packet reception thread'

    while not connection_started:
        time.sleep(1)

    while True:

        length = 0
        data = b''

        while length < 4162:
            d = sock.recv(4162)
            data = b''.join([data, d])
            length = len(data)

        try:
            packet = GCOMM.parse(data)
            c.add_line("< " + str(packet))
            packets.append(packet)

        except:
            c.add_line("< Bad packet recieved." + str(d[:20]))

def run_log(packets, pkl_fname):
    'Continuous logging thread'
    last_len = 0
    while True:
        if len(packets) != last_len:
            if pkl_fname != 'NA':
                last_len = len(packets)
                with open(pkl_fname, 'wb') as pkl_file:
                    pkl.dump(packets, pkl_file)
            else:
                time.sleep(0.1)
        else:
            time.sleep(0.1)

def tui(args):

    packets_arr = []


    global sock
    global connection_started
    global c

    c = Console(splash_art=asciiart)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    sock.settimeout(1)
    try:
        sock.connect((args.host, args.port))
    except socket.timeout:
        return

    sock.settimeout(None)

    connection_started = True

    recv_thread = threading.Thread(target=get_packets, kwargs={"packets":packets_arr}, daemon=True)
    recv_thread.start()

    if (args.logfile != None):
        logging_thread = threading.Thread(target=run_log, kwargs={"packets":packets_arr,"pkl_fname":args.logfile}, daemon=True)
        logging_thread.start()


    try:
        c.start(cmdf=parse)
    except Exception as e:
        c.debug_log(str(e))
        raise
    finally:
        c.cleanup()
        sock.close()
        sys.exit()
