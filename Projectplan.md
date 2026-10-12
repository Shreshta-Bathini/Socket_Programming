# Brief Project Plan

Two programs, two languages:
- **Oracle Node (ON)**: TCP server on port 5000. Reads a config file, tells each VN who its neighbours are.
- **Virtual Node (VN)**: connects to ON over TCP, then runs a link-state protocol with other VNs over UDP.


---


- ON: Shreshta
- VN: Srinithya
- ON language: C++
- VN language: Python
### Setup
- check whether each machine is reachable by the other thru pinging
- are tcp 5000 and udp ports allowed on each machine
- ON uses TCP 5000 and VNs use UDP ports
- single threaded preferred
- Atmost 26 nodes

## Phase 1 - Understanding on paper

Both programs must agree on every byte, so fix these decisions together.

### 1.1 Network graph model
- Draw the 5-node example (A to E) with the costs from the config file.
- Write out the config matrix and the full symmetric adjacency matrix for it.
- Work out by hand what LINK-STATE tuples each node should receive. Example for E: (C, ip, port, 1), (D, ip, port, 7), (E, ip, port, 0).

### 1.2 Framing over TCP
TCP is a byte stream, so a single `recv` can return half a message or two messages. Decide:
- How does the receiver know a message's type? (e.g. a type byte)
- How does it know the message's length? (a length field, or a tuple count)
- How will you loop until you have read exactly the number of bytes you need?

### 1.3 Message formats (fill in the tables yourselves)
Use binary, not strings. Decide byte order (network byte order is the usual choice) and field sizes.

**CONNECT (VN → ON)**

| Field | Size (bytes) | Notes |
|---|---|---|
| type | ? | |
| IP address | ? | |
| UDP port | ? | |

**LINK-STATE (ON → VN)**

| Field | Size (bytes) | Notes |
|---|---|---|
| type | ? | |
| length or tuple count | ? | |
| tuples: node letter, IP, port, cost | ? each | exactly one tuple has cost 0 (the VN itself) |

**LSP (VN ↔ VN, UDP)**

| Field | Size (bytes) | Notes |
|---|---|---|
| originID (letter) | ? | |
| sequence number | ? | |
| neighbour count | ? | |
| neighbours: letter, cost (and IP, port if needed) | ? each | |

- Think about whether a VN needs the IP and port of non-neighbours. (It only sends LSPs to its direct neighbours, so it needs the IP and port of neighbours only.)
- Check that the biggest possible message (26 nodes) fits in one UDP datagram.

### 1.4 State each program must hold
- ON: list of connected VNs (socket, IP, port, assigned letter), the parsed cost matrix, the config file's last modification time.
- VN: own letter, own neighbour list, own sequence number, and a table of the latest LSP seen per origin.

### 1.5 Protocol behaviour decisions
- When exactly does ON send LINK-STATE? (After N CONNECTs arrive, and after every config change.)
- What does ON do with extra connections beyond N? (They are islands with no neighbours.)
- When does a VN send an LSP? (On each new LINK-STATE, and periodically every 10 to 20 s.)
- When does a VN forward a received LSP? (Only if its sequence number is newer than the stored one, and to all neighbours except the sender.)
- How often does a VN print its graph, and in what format? (Similar to the config file.)

### 1.6 Test plan (write it now)
- Build multiple testcases

---

## Phase 2: Oracle Node

1. Read the config file path from the command-line argument.
2. Parse the file: skip comments (#), blank lines and leading tabs, read the upper-triangle rows, and mirror them into a full matrix. Add sanity checks (row count, value ranges).
3. Print the parsed matrix to check it against your hand-drawn version.
4. Create a TCP listening socket on port 5000 (set address reuse so restarts work).
5. Set up a `select` loop (with a sleep or timeout) over the listening socket and the client sockets.
6. Accept connections and assign letters in order (A, then B, and so on).
7. Read CONNECT messages using your framing and store the IP and port per node.
8. When N nodes have sent CONNECT, build and send each node's LINK-STATE message.
9. Handle disconnects and extra connections without crashing.
10. Periodically check the config file's modification time. If it changed, re-parse and resend LINK-STATE to every VN.

---

## Phase 3: Virtual Node, TCP part 

1. Parse the command-line arguments: ON IP, own UDP port, and optionally own IP.
2. Create and bind the UDP socket, and exit with a clear error message on failure.
3. Connect via TCP to ON on port 5000.
4. Send the CONNECT message immediately after connecting.
5. Wait for LINK-STATE, read it using your framing, and decode the tuples.
6. Print the neighbourhood in readable form, e.g. `E=0,C=1,D=7`.
7. Test ON and VN together, first with 2 nodes and then with all 5.

---

## Phase 4: Link-state protocol (UDP)

1. Build the LSP table (latest sequence number and neighbour list per origin).
2. On a new LINK-STATE from ON: increment your sequence number, update your own entry, and send an LSP to every neighbour (2 or 3 copies each to cover UDP loss).
3. In the main `select` loop, also watch the UDP socket.
4. On receiving an LSP: decode it, compare its sequence number with the stored one, and if newer, store it and forward it to all neighbours except the sender. Otherwise drop it.
5. Add a periodic timer (10 to 20 s) that resends your own LSP.
6. Add a periodic print of the full known graph in the config-file style.
7. Check that every VN's printed graph matches the ON's config.

---

## Phase 5: Integration and testing

1. Run the whole test plan from section 1.6.
2. Edit the config file during the run and check that every VN's graph updates within one or two periods.
3. Test a late-joining VN, extra island nodes, and a link set to -1.
4. Run across two physical machines.
5. Check for leaks: sockets are closed, and the process stays stable after a long run.

---

## Phase 6: Demo preparation

1. Each of you should be able to explain every file in both programs, including the message formats and the `select` loop.
2. Practice making small live changes without internet, e.g. adding a field to a message, or changing the print format or the period.
3. Prepare a demo script: start ON, start the VNs one by one, show printed output, edit the config, and show the update.
4. Have the config file, a network diagram and your message format tables ready.

---
