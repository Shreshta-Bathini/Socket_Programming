# Socket Programming

## Directory Structure

```text
SocketProgramming/
├── Makefile
├── Server.cpp
├── config.txt
├── README.md
└── vn/
    ├── vn.py
    ├── messages.py
    └── linkstate.py
```

- `Server.cpp`: Oracle Node implementation.
- `Makefile`: Compiles the C++ program.
- `config.txt`: Network topology configuration.
- `vn/vn.py`: Virtual Node implementation.
- `vn/messages.py`: Message encoding and decoding.
- `vn/linkstate.py`: Link-state database and topology handling.

## Requirements

- C++ compiler (`g++`)
- GNU Make
- Python 3

## Running the Programs

**1. Compile the Oracle Node**

From the project root:

```bash
make
```

**2. Start the Oracle Node**

```bash
./on config.txt
```

**3. Start each Virtual Node**

Run each VN in a separate terminal:

```bash
python3 vn/vn.py <ON_IP> <VN_IP> <UDP_PORT>
```

Replace the arguments with the appropriate IP addresses and UDP port.

## Communication

The Oracle Node distributes neighbourhood information over TCP. Virtual Nodes exchange link-state information directly over UDP.

