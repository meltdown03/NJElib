#!/usr/bin/env python3
"""
njebrute.py - NJE Node Name Brute Forcer

Tests a list of RHOST node names against one or more NJE servers
to discover valid NJE node names accepted by the target.

Usage (standard positional mode):
    njebrute.py <ip> <port> <ohost> <rhost_file>

Usage (multi-target mode via --targets):
    njebrute.py --targets <targets_file> <rhost_file>

    targets_file format (one entry per line, # lines ignored):
        ip:OHOST           (port defaults to 175)
        ip:port:OHOST
"""

import sys
import argparse
import njelib


def build_parser():
    parser = argparse.ArgumentParser(
        prog="njebrute.py",
        description=(
            "NJE Node Name Brute Forcer. Tests RHOST node names against an NJE "
            "server to discover valid node names accepted by the target."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  # Standard mode — positional args (ip, port, ohost, rhost_file):
  %(prog)s xxx.yyy.com 175 JES2TS01 ~/nje_nodes.txt

  # Multi-target mode — supply a targets file instead of ip/port/ohost:
  %(prog)s --targets targets.txt ~/nje_nodes.txt

targets file format (one entry per line):
  xxx.yyy.com:JES2TS01          # port defaults to 175
  zzz.aaa.com:2175:NODENAME1    # explicit port
  # lines starting with # are ignored
""",
    )

    # --targets makes the three positionals optional
    using_targets = "--targets" in sys.argv

    if not using_targets:
        parser.add_argument(
            "ip",
            help="Target IP address or hostname of the NJE server",
        )
        parser.add_argument(
            "port",
            type=int,
            help="Target port (NJE default is 175)",
        )
        parser.add_argument(
            "ohost",
            help="Local NJE node name sent as OHOST in the signon",
        )

    parser.add_argument(
        "rhost_file",
        help="File containing RHOST node names to test, one per line",
    )

    parser.add_argument(
        "--targets",
        metavar="FILE",
        help=(
            "File of ip:OHOST or ip:port:OHOST pairs to test against, one per line. "
            "When supplied, the ip, port, and ohost positional arguments are not used. "
            "Port defaults to 175 when not included in the entry."
        ),
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=2,
        metavar="SECS",
        help="Connection timeout in seconds (default: 2)",
    )
    parser.add_argument(
        "--debug",
        type=int,
        default=1,
        metavar="LEVEL",
        help="NJE debug verbosity level (default: 1)",
    )

    return parser


def read_targets(path):
    """Parse a targets file into a list of (ip, port, ohost) tuples."""
    targets = []
    try:
        with open(path) as f:
            for lineno, raw in enumerate(f, 1):
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split(":")
                if len(parts) == 2:
                    ip, ohost = parts
                    port = 175
                elif len(parts) == 3:
                    ip, port_s, ohost = parts
                    try:
                        port = int(port_s)
                    except ValueError:
                        print(f"[!] Bad port on line {lineno}: {line!r} — skipping")
                        continue
                else:
                    print(f"[!] Malformed entry on line {lineno}: {line!r} — skipping")
                    continue
                targets.append((ip.strip(), port, ohost.strip()))
    except IOError as e:
        print(f"[!] Error reading targets file: {e}")
        sys.exit(1)
    return targets


def read_rhosts(path):
    """Return a list of RHOST node names from a file, skipping blanks and comments."""
    try:
        with open(path) as f:
            return [
                line.strip()
                for line in f
                if line.strip() and not line.strip().startswith("#")
            ]
    except IOError as e:
        print(f"[!] Error reading rhost file: {e}")
        sys.exit(1)


def test_rhost(ip, port, ohost, rhost, timeout, debug):
    """Attempt an NJE session for a single RHOST and return 'pass' or 'fail'."""
    print(f"\n[*] Testing RHOST: {rhost}")
    nje = njelib.NJE(rhost, ohost)
    nje.set_debuglevel(debug)
    try:
        connected = nje.session(host=ip, port=port, timeout=timeout)
        return "pass" if connected else "fail"
    except Exception as e:
        print(f"[!] Exception: {e}")
        return "fail"


def main():
    parser = build_parser()
    args = parser.parse_args()

    rhosts = read_rhosts(args.rhost_file)

    results = []

    if args.targets:
        targets = read_targets(args.targets)
        if not targets:
            print("[!] No valid targets found in targets file.")
            sys.exit(1)
        for ip, port, ohost in targets:
            for rhost in rhosts:
                status = test_rhost(ip, port, ohost, rhost, args.timeout, args.debug)
                results.append((ip, ohost, rhost, status))
    else:
        for rhost in rhosts:
            status = test_rhost(args.ip, args.port, args.ohost, rhost, args.timeout, args.debug)
            results.append((args.ip, args.ohost, rhost, status))

    print("\n" + "=" * 40)
    print("RESULTS:")
    print("=" * 40)
    for ip, ohost, rhost, status in results:
        if args.targets:
            print(f"{ip} ({ohost}) -> {rhost}: {status}")
        else:
            print(f"{rhost}: {status}")


if __name__ == "__main__":
    main()
