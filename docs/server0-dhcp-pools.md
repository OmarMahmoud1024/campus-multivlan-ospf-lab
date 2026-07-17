# Server0 DHCP configuration

`Server0` is a Packet Tracer `Server-PT` device, not an IOS router, so its
DHCP service isn't configured with `ip dhcp pool` CLI commands - it's set up
through the server's **Desktop > IP Configuration** and **Services > DHCP**
tabs. This file documents exactly what to enter there.

## Server0 itself

| Setting | Value |
|---|---|
| IP Address | 192.168.100.10 |
| Subnet Mask | 255.255.255.0 |
| Default Gateway | 192.168.100.1 |

## DHCP pools (Services > DHCP tab)

The lab spec requires the DHCP server to serve **every VLAN except the
devices hanging off S4 and S5** (PC10 and PC11, which get static IPs
instead - see `docs/addressing-table.md`). That means five pools: one per
VLAN with end-user PCs. VLAN 100 doesn't need a pool since only the server
itself lives there, and it's statically addressed.

| Pool name | VLAN | Default Gateway | Start IP | Subnet Mask | Max Users |
|---|---|---|---|---|---|
| POOL_VLAN10 | 10 | 192.168.10.1 | 192.168.10.11 | 255.255.255.0 | 50 |
| POOL_VLAN20 | 20 | 192.168.20.1 | 192.168.20.11 | 255.255.255.0 | 50 |
| POOL_VLAN30 | 30 | 192.168.30.1 | 192.168.30.11 | 255.255.255.0 | 50 |
| POOL_VLAN40 | 40 | 192.168.40.1 | 192.168.40.11 | 255.255.255.0 | 50 |
| POOL_VLAN50 | 50 | 192.168.50.1 | 192.168.50.11 | 255.255.255.0 | 50 |

`.2`-`.10` in each subnet are left out of the pool as a reserved block
(gateway is `.1`; the rest is headroom for anything that needs a static
address later without colliding with a lease).

## Why DHCP relay is needed

Server0 only lives on VLAN 100. A DHCP `DISCOVER` broadcast from, say,
PC4 on VLAN 10 never reaches it on its own - broadcasts don't cross router
boundaries. Each router subinterface that fronts a DHCP-served VLAN carries
an `ip helper-address 192.168.100.10` line, which unicasts the DHCP
broadcast to the server and relays the response back. See:

- `R1.txt` - Gi0/0.10 and Gi0/0.20
- `R2.txt` - Gi0/3.50 (Gi0/3.100 doesn't need it, the server is local there)
- `R3.txt` - Gi0/1.30 and Gi0/1.40

R4 and R5 deliberately have **no** `ip helper-address` anywhere, since
PC10 and PC11 are explicitly excluded from DHCP by the lab requirements.
