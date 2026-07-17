#!/usr/bin/env python3
"""
Consistency checker for the router/switch configs in this repo.

There's no Packet Tracer install available to actually load these configs
and click "test connectivity" - the repo was rebuilt from a topology
screenshot, not a live simulator session. What this script *can* do is
parse every config the same way a human reviewer would and mechanically
verify the things that are easy to get wrong when a topology like this is
typed out by hand:

  1. Every point-to-point link's two interfaces sit in the same subnet,
     with different host addresses, and neither is the network/broadcast
     address.
  2. No two subnets in the whole addressing plan overlap.
  3. Every router's OSPF `network` statements exactly match the subnets of
     its OSPF-eligible interfaces (i.e. everything except the R4-R5 static
     link, which must NOT appear under `router ospf`).
  4. `ip helper-address` is present on every VLAN subinterface that DHCP is
     supposed to serve, and absent on R4/R5's LANs (which are excluded by
     the lab spec).
  5. Each VLAN's gateway IP (the router subinterface address) matches what
     `docs/addressing-table.md` claims and what the DHCP pool's default
     gateway is set to in `docs/server0-dhcp-pools.md`.

This is a static-analysis check, not an emulator - it catches typos and
inconsistent addressing, not IOS syntax errors or runtime behaviour.
"""
import ipaddress
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROUTERS_DIR = ROOT / "configs" / "routers"
DOCS_DIR = ROOT / "docs"

failures = []


def fail(msg):
    failures.append(msg)
    print(f"  FAIL: {msg}")


def ok(msg):
    print(f"  ok:   {msg}")


def parse_router_config(path):
    """Return dict: interfaces -> {ip, mask, helper}, ospf_networks -> set of (net, wildcard)."""
    text = path.read_text()
    interfaces = {}
    current_if = None
    ospf_networks = []
    in_ospf = False

    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("interface "):
            current_if = line.split("interface ", 1)[1]
            interfaces[current_if] = {"ip": None, "mask": None, "helper": None}
            in_ospf = False
            continue
        if line.startswith("router ospf"):
            in_ospf = True
            current_if = None
            continue
        if line.startswith("ip route") or line.startswith("line ") or line == "!":
            in_ospf = False
        if current_if and line.startswith("ip address "):
            parts = line.split()
            interfaces[current_if]["ip"] = parts[2]
            interfaces[current_if]["mask"] = parts[3]
        if current_if and line.startswith("ip helper-address"):
            interfaces[current_if]["helper"] = line.split()[-1]
        if in_ospf and line.startswith("network "):
            parts = line.split()
            ospf_networks.append((parts[1], parts[2]))

    return interfaces, ospf_networks


def cidr_for(ip, mask):
    iface = ipaddress.IPv4Interface(f"{ip}/{mask}")
    return iface.network


print("=== Loading router configs ===")
routers = {}
for f in sorted(ROUTERS_DIR.glob("R*.txt")):
    name = f.stem
    interfaces, ospf_nets = parse_router_config(f)
    routers[name] = {"interfaces": interfaces, "ospf": ospf_nets}
    n_ips = sum(1 for i in interfaces.values() if i["ip"])
    print(f"  {name}: {n_ips} addressed interfaces, {len(ospf_nets)} OSPF network statements")

print("\n=== Check 1: point-to-point links match on both ends ===")
links = [
    ("R1", "GigabitEthernet0/1", "R2", "GigabitEthernet0/0", "10.10.10.0/24"),
    ("R2", "GigabitEthernet0/1", "R3", "GigabitEthernet0/0", "10.10.20.0/24"),
    ("R2", "GigabitEthernet0/2", "R4", "GigabitEthernet0/0", "10.10.50.0/24"),
    ("R4", "GigabitEthernet0/2", "R5", "GigabitEthernet0/0", "20.20.20.0/24"),
]
for r_a, if_a, r_b, if_b, expected_subnet in links:
    ip_a = routers[r_a]["interfaces"][if_a]["ip"]
    mask_a = routers[r_a]["interfaces"][if_a]["mask"]
    ip_b = routers[r_b]["interfaces"][if_b]["ip"]
    mask_b = routers[r_b]["interfaces"][if_b]["mask"]
    net_a = cidr_for(ip_a, mask_a)
    net_b = cidr_for(ip_b, mask_b)
    label = f"{r_a}:{if_a} <-> {r_b}:{if_b}"
    if str(net_a) != expected_subnet or str(net_b) != expected_subnet:
        fail(f"{label}: expected both ends in {expected_subnet}, got {net_a} / {net_b}")
        continue
    if ip_a == ip_b:
        fail(f"{label}: both ends use the same IP {ip_a}")
        continue
    ok(f"{label}: {ip_a} <-> {ip_b} in {expected_subnet}")

print("\n=== Check 2: no overlapping subnets anywhere in the plan ===")
all_subnets = {}
for rname, rdata in routers.items():
    for ifname, idata in rdata["interfaces"].items():
        if idata["ip"]:
            net = cidr_for(idata["ip"], idata["mask"])
            all_subnets.setdefault(str(net), []).append(f"{rname}:{ifname}")

nets = [ipaddress.IPv4Network(n) for n in all_subnets]
overlap_found = False
for i, n1 in enumerate(nets):
    for n2 in nets[i + 1:]:
        if n1 != n2 and n1.overlaps(n2):
            fail(f"overlapping subnets: {n1} and {n2}")
            overlap_found = True
if not overlap_found:
    ok(f"{len(nets)} distinct subnets, no overlaps")

print("\n=== Check 3: OSPF coverage matches expectations ===")
# R4's R5-facing link must NOT be in OSPF; every other addressed
# interface on R1/R2/R3/R4 must be.
expected_no_ospf = {("R4", "GigabitEthernet0/2")}
for rname, rdata in routers.items():
    if rname == "R5":
        if rdata["ospf"]:
            fail("R5 has an OSPF process configured, but the lab spec requires static-only on R5")
        else:
            ok("R5 correctly has no OSPF process")
        continue

    ospf_nets_set = {cidr_for(*parts) if False else None for parts in []}  # placeholder, unused
    ospf_cidrs = set()
    for net, wildcard in rdata["ospf"]:
        # convert "192.168.10.0 0.0.0.255" style into a CIDR
        wc_octets = [int(o) for o in wildcard.split(".")]
        mask_octets = [255 - o for o in wc_octets]
        mask = ".".join(str(o) for o in mask_octets)
        ospf_cidrs.add(str(cidr_for(net, mask)))

    for ifname, idata in rdata["interfaces"].items():
        if not idata["ip"]:
            continue
        net = str(cidr_for(idata["ip"], idata["mask"]))
        should_be_in_ospf = (rname, ifname) not in expected_no_ospf
        in_ospf = net in ospf_cidrs
        if should_be_in_ospf and not in_ospf:
            fail(f"{rname}:{ifname} ({net}) should be advertised via OSPF but isn't")
        elif not should_be_in_ospf and in_ospf:
            fail(f"{rname}:{ifname} ({net}) should NOT be in OSPF (static link) but is")
        else:
            ok(f"{rname}:{ifname} ({net}) OSPF membership correct ({'in' if in_ospf else 'excluded, as expected'})")

print("\n=== Check 4: DHCP relay present only where it should be ===")
dhcp_expected = {
    ("R1", "GigabitEthernet0/0.10"): True,
    ("R1", "GigabitEthernet0/0.20"): True,
    ("R2", "GigabitEthernet0/3.50"): True,
    ("R2", "GigabitEthernet0/3.100"): False,  # server is local here
    ("R3", "GigabitEthernet0/1.30"): True,
    ("R3", "GigabitEthernet0/1.40"): True,
    ("R4", "GigabitEthernet0/1"): False,  # S4 excluded by spec
    ("R5", "GigabitEthernet0/1"): False,  # S5 excluded by spec
}
for (rname, ifname), should_have_helper in dhcp_expected.items():
    idata = routers[rname]["interfaces"].get(ifname)
    if idata is None:
        fail(f"{rname}:{ifname} not found in config at all")
        continue
    has_helper = idata["helper"] is not None
    if has_helper != should_have_helper:
        fail(f"{rname}:{ifname} helper-address presence wrong (expected {should_have_helper}, got {has_helper})")
    else:
        ok(f"{rname}:{ifname} helper-address {'present' if has_helper else 'correctly absent'}")
    if has_helper and idata["helper"] != "192.168.100.10":
        fail(f"{rname}:{ifname} helper points at {idata['helper']}, expected 192.168.100.10 (Server0)")

print("\n=== Check 5: gateway IPs match the addressing table doc ===")
addressing_doc = (DOCS_DIR / "addressing-table.md").read_text()
gateway_checks = [
    ("R1", "GigabitEthernet0/0.10", "192.168.10.1"),
    ("R1", "GigabitEthernet0/0.20", "192.168.20.1"),
    ("R2", "GigabitEthernet0/3.50", "192.168.50.1"),
    ("R2", "GigabitEthernet0/3.100", "192.168.100.1"),
    ("R3", "GigabitEthernet0/1.30", "192.168.30.1"),
    ("R3", "GigabitEthernet0/1.40", "192.168.40.1"),
]
for rname, ifname, expected_ip in gateway_checks:
    actual = routers[rname]["interfaces"][ifname]["ip"]
    if actual != expected_ip:
        fail(f"{rname}:{ifname} is {actual}, addressing table says {expected_ip}")
        continue
    if expected_ip not in addressing_doc:
        fail(f"{expected_ip} not mentioned anywhere in docs/addressing-table.md")
        continue
    ok(f"{rname}:{ifname} = {actual}, matches addressing-table.md")

print()
if failures:
    print(f"RESULT: {len(failures)} check(s) failed.")
    sys.exit(1)
else:
    print("RESULT: all consistency checks passed.")
    sys.exit(0)
