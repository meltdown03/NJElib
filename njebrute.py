#!/usr/bin/env python3

import sys
import njelib

def usage():
    print(f"Usage: {sys.argv[0]} <host> <port> <ohost> <nodefile>")
    print(f"  host     - Target hostname or IP")
    print(f"  port     - Target port (typically 175)")
    print(f"  ohost    - Local node name (e.g. JES2TS01)")
    print(f"  nodefile - File containing RHOST node names to test, one per line")
    sys.exit(1)

if len(sys.argv) < 5:
    usage()

host     = sys.argv[1]
port     = int(sys.argv[2])
ohost    = sys.argv[3]
nodefile = sys.argv[4]

try:
    with open(nodefile, 'r') as f:
        nodes = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    print(f"[!] Node file not found: {nodefile}")
    sys.exit(1)

for rhost in nodes:
    print(f"[*] Testing RHOST: {rhost}")
    nje = njelib.NJE(rhost, ohost)
    nje.set_debuglevel(1)
    result = nje.session(host=host, port=port, timeout=2)
    if result:
        print(f"[+] SUCCESS: {rhost} accepted!")
    else:
        print(f"[-] Failed: {rhost}")
