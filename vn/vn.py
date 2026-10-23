#vn.py - 
#Usage: python3 vn.py on_ip vn_ip udp_port
import select #waits on several sockets at once
#single threaded, event driven
import socket
import sys
import time

import messages #our file messages.py
from linkstate import LinkStateDB #from file linkstate.py
ON_TCP_PORT = 5000 #vn connects to on at port 5000
SELECT_TIMEOUT = 1.0 
LSP_PERIOD = 30.0 #gap between periodic LSPs
LSP_COPIES = 2 #send each one 2 times. in case udp drops one

def parse_args():
    if len(sys.argv) != 4:
        print("usage: python3 vn.py <ON_IP> <MY_IP> <MY_UDP_PORT>")
        sys.exit(1)
    on_ip = sys.argv[1]
    my_ip = sys.argv[2]
    try:
        my_port = int(sys.argv[3])
    except ValueError:
        print("error: UDP port must be a number")
        sys.exit(1)
    if not ( 0 < my_port < 65536):
        print("error: UDP port must be between 1 and 65535")
        sys.exit(1)
    if my_ip in ("127.0.0.1", "0.0.0.0") or on_ip in ("127.0.0.1", "0.0.0.0"):
        print("error: do not use loopback or 0.0.0.0 addresses")
        sys.exit(1)
    return on_ip, my_ip, my_port

def open_udp_socket(my_ip, my_port):
    #creating udp sockets later used for lsps. exiting if port is taken
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind((my_ip,my_port))
    except OSError as e:
        print("error: cannot bind UDP socket to %s:%d (%s)" % (my_ip, my_port, e))
        sys.exit(1)
    return sock

def connect_to_oracle(on_ip, my_ip, my_port):
    #make tcp connection to on and send connect msg
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((on_ip, ON_TCP_PORT))
    except OSError as e:
        print("error: cannot connect to ON at %s:%d (%s)" % (on_ip, ON_TCP_PORT, e))
        sys.exit(1)
    
    sock.sendall(messages.pack_connect(my_ip, my_port))
    print("connected to ON, sent CONNECT (%s:%d)" % (my_ip, my_port))
    return sock

def print_neighbourhood(tuples):
    #in the tuples exactly one has a cost of 0, which is the current vn, print that first and then the neighbours
    me = [t for t in tuples if t[3]==0]
    others = [t for t in tuples if t[3]!=0]
    print(",".join("%s=%d" % (t[0],t[3]) for t in me + others))

def send_lsp(udp_sock, lsp_bytes, targets):
    for addr in targets:
        for _ in range(LSP_COPIES):
            try:
                udp_sock.sendto(lsp_bytes, addr)
            except OSError as e:
                print("warning: could not send LSP to %s:%d (%s)" % (addr[0], addr[1],e))

def announce_own_lsp(udp_sock, db):
    origin, seq, links = db.build_own_lsp()
    lsp_bytes = messages.pack_lsp(origin, seq, links)
    send_lsp(udp_sock, lsp_bytes, db.forward_targets(None))               

def main():
    on_ip, my_ip, my_port = parse_args()
    udp_sock = open_udp_socket(my_ip, my_port)
    tcp_sock = connect_to_oracle(on_ip, my_ip, my_port)
    tcp_buffer = b"" #bytes received from on but not decoded yet
    db = LinkStateDB() #who i am, my neighbours, newest lsp from every node
    next_period = time.monotonic() + LSP_PERIOD #when is the timer triggered again

    while True:
        readable, _, _ = select.select([tcp_sock, udp_sock], [], [], SELECT_TIMEOUT)

        for sock in readable:
            if sock is tcp_sock:
                data = tcp_sock.recv(4096)
                if not data:
                    print("ON closed the connection, exiting")
                    return 
                tcp_buffer += data
                #keep extracting until nothing is left
                while True:
                    tuples, tcp_buffer = messages.extract_link_state(tcp_buffer)
                    if tuples is None:
                        break
                    print_neighbourhood(tuples)
                    db.set_neighbourhood(tuples)
                    announce_own_lsp(udp_sock, db)
                    next_period = time.monotonic() + LSP_PERIOD
            
            elif sock is udp_sock:
                #need to decode the lsp, update link state
                data, addr = udp_sock.recvfrom(2048)
                try:
                    origin, seq, links = messages.unpack_lsp(data)
                except ValueError as e:
                    print("ignoring bad UDP packet from %s:%d (%s)" % (addr[0], addr[1], e))
                    continue
                if db.accept_lsp(origin, seq, links):
                    send_lsp(udp_sock, data, db.forward_targets(addr))
        now = time.monotonic()
        if now >= next_period:
            next_period = now + LSP_PERIOD
            if db.me is not None:
                announce_own_lsp(udp_sock, db)
                print(db.graph_text())
if __name__ == "__main__":
    main()