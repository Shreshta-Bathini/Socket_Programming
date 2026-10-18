#messages.py - byte formats for ON <-> VN messages
import socket
import struct
MSG_CONNECT = 1
MSG_LINK_STATE = 2
CONNECT_FMT = "!B4sH"
LS_HEADER_FMT = "!BB"
LS_TUPLE_FMT = "!c4sHI"
LS_HEADER_SIZE = struct.calcsize(LS_HEADER_FMT)
LS_TUPLE_SIZE = struct.calcsize(LS_TUPLE_FMT)

def pack_connect(ip, udp_port):
    return struct.pack(CONNECT_FMT, MSG_CONNECT, socket.inet_aton(ip), udp_port)
def pack_link_state(tuples):
    data = struct.pack(LS_HEADER_FMT, MSG_LINK_STATE, len(tuples))
    for letter, ip, port, cost in tuples:
        data += struct.pack(LS_TUPLE_FMT, letter.encode(), socket.inet_aton(ip), port, cost)
    return data

def extract_link_state(buffer):
    if len(buffer) < LS_HEADER_SIZE:
        return None, buffer
    msg_type , count = struct.unpack_from(LS_HEADER_FMT, buffer, 0)
    if msg_type != MSG_LINK_STATE:
        raise ValueError("unexpected message type %d from ON" % msg_type)
    total = LS_HEADER_SIZE + count * LS_TUPLE_SIZE
    if len(buffer) < total:
        return None, buffer
    tuples = []
    offset = LS_HEADER_SIZE
    for _ in range(count):
        letter, ip, port, cost = struct.unpack_from(LS_TUPLE_FMT, buffer, offset)
        tuples.append((letter.decode(), socket.inet_ntoa(ip), port, cost))
        offset += LS_TUPLE_SIZE
    return tuples, buffer[total:]
    #add test_messages.py before running testcases