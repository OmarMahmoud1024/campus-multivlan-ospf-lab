# Addressing table

## VLANs / access subnets

| VLAN | Name | Subnet | Gateway | Switch | Router | Hosts | Addressing |
|---|---|---|---|---|---|---|---|
| 10 | SALES | 192.168.10.0/24 | 192.168.10.1 | S1 | R1 (Gi0/0.10) | PC4, PC5 | DHCP |
| 20 | IT | 192.168.20.0/24 | 192.168.20.1 | S1 | R1 (Gi0/0.20) | PC6 | DHCP |
| 30 | HR | 192.168.30.0/24 | 192.168.30.1 | S3 | R3 (Gi0/1.30) | PC0, PC1 | DHCP |
| 40 | FINANCE | 192.168.40.0/24 | 192.168.40.1 | S3 | R3 (Gi0/1.40) | PC2, PC3 | DHCP |
| 50 | ENGINEERING | 192.168.50.0/24 | 192.168.50.1 | S2 | R2 (Gi0/3.50) | PC8, PC9 | DHCP |
| 100 | SERVERS | 192.168.100.0/24 | 192.168.100.1 | S2 | R2 (Gi0/3.100) | Server0 (.10) | Static |

## Flat LANs excluded from DHCP

| Segment | Subnet | Gateway | Switch | Router | Host | Addressing |
|---|---|---|---|---|---|---|
| S4 LAN | 172.16.0.0/16 | 172.16.0.1 | S4 | R4 (Gi0/1) | PC10 | Static: 172.16.0.10 /16, gw 172.16.0.1 |
| S5 LAN | 192.168.200.0/24 | 192.168.200.1 | S5 | R5 (Gi0/1) | PC11 | Static: 192.168.200.10 /24, gw 192.168.200.1 |

## Router-to-router (WAN) links

| Link | Subnet | Side A | Side B | Routing |
|---|---|---|---|---|
| R1 - R2 | 10.10.10.0/24 | R1 Gi0/1 = .1 | R2 Gi0/0 = .2 | OSPF area 0 |
| R2 - R3 | 10.10.20.0/24 | R2 Gi0/1 = .1 | R3 Gi0/0 = .2 | OSPF area 0 |
| R2 - R4 | 10.10.50.0/24 | R2 Gi0/2 = .1 | R4 Gi0/0 = .2 | OSPF area 0 |
| R4 - R5 | 20.20.20.0/24 | R4 Gi0/2 = .1 | R5 Gi0/0 = .2 | Static only (per lab spec) |

## How R5's subnet stays reachable without OSPF on that link

The lab requirement is explicit: R4-R5 uses static routing, everything
else uses OSPF. Two static routes make that link fully reachable without
turning it into an OSPF adjacency:

- **R4**: `ip route 192.168.200.0 255.255.255.0 20.20.20.2`, then
  `redistribute static subnets` under `router ospf 1` so R1/R2/R3 learn
  about 192.168.200.0/24 as an OSPF external route without R4-R5 ever
  running OSPF between themselves.
- **R5**: `ip route 0.0.0.0 0.0.0.0 20.20.20.1` - a default route back
  toward the OSPF backbone, since R5 has nothing to run OSPF with anyway.

## Router IDs

| Router | OSPF Router ID |
|---|---|
| R1 | 1.1.1.1 |
| R2 | 2.2.2.2 |
| R3 | 3.3.3.3 |
| R4 | 4.4.4.4 |
| R5 | n/a - no OSPF process |

## Credentials

| Device type | Enable secret | Console / VTY |
|---|---|---|
| Routers (R1-R5) | lab123 | lab123 |
| Switches (S1-S5) | lab456 | lab456 |

`service password-encryption` is enabled on every device so these don't
sit in plaintext in the running-config.
