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
LSP_HEADER_FMT = "!cIB"
LSP_LINK_FMT = "!cI"
LSP_HEADER_SIZE = struct.calcsize(LSP_HEADER_FMT)
LSP_LINK_SIZE = struct.calcsize(LSP_LINK_FMT)

def pack_lsp(origin, seq, links):
    data = struct.pack(LSP_HEADER_FMT, origin.encode(), seq, len(links))
    for nbr in sorted(links):
        data += struct.pack(LSP_LINK_FMT, nbr.encode(), links[nbr])
    return data
def unpack_lsp(data):
    if len(data) < LSP_HEADER_SIZE:
        raise ValueError("LSP too short")
    origin, seq, count = struct.unpack_from(LSP_HEADER_FMT, data, 0)
    if len(data) != LSP_HEADER_SIZE + count * LSP_LINK_SIZE:
        raise ValueError("LSP length does not match link count")
    links = {}
    offset = LSP_HEADER_SIZE
    for _ in range(count):
        nbr, cost = struct.unpack_from(LSP_LINK_FMT, data, offset)
        links[nbr.decode()] = cost
        offset += LSP_LINK_SIZE
    return origin.decode(), seq, links