# 01 — Azure Hub-and-Spoke with FortiGate NVA

```
                 On-prem ──IPsec/ER──► [GatewaySubnet: VPN/ER GW]
                                               │ (UDR: spokes → FGT ILB)
Internet ─► [ELB / PIP] ─► FortiGate-A / FortiGate-B (A/P or A/A)
                               │ port1 external   │ port2 internal
                               └──── [ILB HA ports: 10.0.2.4] ────┐
         HUB VNet 10.0.0.0/16  (AzureBastionSubnet, AppGW subnet) │
        ───────────── peering (non-transitive) ───────────────────┤
   Spoke-A 10.1.0.0/16  UDR 0/0 → 10.0.2.4     Spoke-B 10.2.0.0/16  UDR 0/0 → 10.0.2.4
```

## Fundamentals

### Q1. What is hub-and-spoke and why use it?
A central **hub VNet** holds shared services — firewall/NVA, VPN/ExpressRoute gateway, Bastion, DNS — and workload **spoke VNets** peer to it. Benefits: one inspection and egress point, shared connectivity, workload isolation per spoke/subscription, and central governance. Trade-off: the hub NVA becomes a chokepoint, so it must be HA and sized for throughput.

### Q2. Is VNet peering transitive?
No. Spoke-A ↔ Hub and Hub ↔ Spoke-B does **not** give Spoke-A ↔ Spoke-B. You need either a UDR pointing spoke-to-spoke traffic at the hub NVA (with *Allow forwarded traffic* on peerings), a direct spoke-to-spoke peering, Azure Virtual Network Manager connected groups, or Virtual WAN.

### Q3. What peering settings matter in hub-spoke?
- **Allow virtual network access** — basic connectivity.
- **Allow forwarded traffic** — accept traffic not originating in the peer VNet (needed when the NVA forwards spoke-to-spoke).
- **Allow gateway transit** — set on the **hub** side so spokes can use the hub's VPN/ER gateway.
- **Use remote gateways** — set on the **spoke** side. A spoke can't have its own gateway if it uses remote gateways.

### Q4. How do you force spoke traffic through the FortiGate?
Associate a **route table (UDR)** with spoke subnets: `0.0.0.0/0 → Virtual appliance → <FortiGate ILB frontend IP>` plus routes for other spokes and on-prem prefixes. Set **"Propagate gateway routes" = No** on spoke route tables so BGP-learned on-prem routes don't bypass the firewall. Enable **IP forwarding** on the FortiGate NICs (Azure NIC setting) — FortiOS handles the OS side.

### Q5. How does on-prem → spoke traffic get inspected?
Put a route table on **GatewaySubnet** with spoke prefixes → FortiGate ILB IP. Otherwise the gateway routes directly into the spoke via peering and the return path goes through the firewall → **asymmetric routing**, which a stateful firewall drops.

### Q6. What subnets live in the hub?
`GatewaySubnet` (exact name, /27 or larger recommended), `AzureBastionSubnet` (exact name, /26 minimum), FortiGate external, FortiGate internal, HA-sync/management (for A/P), Application Gateway subnet (dedicated), optionally `AzureFirewallSubnet`, DNS Private Resolver inbound/outbound subnets.

### Q7. What is UDR vs system route vs BGP route precedence?
Azure picks the **longest prefix match** first. For equal prefixes the order is **UDR > BGP > system route**. That's why a /16 learned via BGP beats a 0/0 UDR — you must add specific UDRs for on-prem/other spokes or disable gateway route propagation.

## FortiGate NVA high availability

### Q8. How do you deploy FortiGate HA in Azure?
Two common designs from the Fortinet Azure reference:
1. **Active-Passive with Azure Load Balancers** (recommended): external Standard LB for inbound, internal Standard LB with **HA ports** rule for east-west/egress. Health probes detect the active unit; failover in seconds. Config sync via FGCP over a dedicated HA subnet.
2. **Active-Passive with SDN connector failover**: on failover the passive unit calls Azure API to move public IP and rewrite UDRs — slower (tens of seconds) but no LB.
3. **Active-Active** behind LBs: more throughput, but sessions aren't synced the same way — you need SNAT or LB symmetric hashing to keep flows on the same unit.

### Q9. What is an ILB HA ports rule?
A Standard internal Load Balancer rule with **protocol = All, port = 0**, load-balancing every TCP/UDP flow on all ports. It lets the UDR point at one frontend IP while the LB sends flows to the healthy FortiGate. Only on **Standard** SKU internal LBs.

### Q10. How do you avoid asymmetric routing with an NVA?
- Make both directions traverse the **same ILB** (Azure LB hashes symmetrically for HA-ports).
- UDRs on *both* sides (GatewaySubnet and spokes).
- For inbound from internet via ELB, **SNAT** on FortiGate so return traffic comes back through the same unit.
- Don't let BGP routes bypass the firewall (disable gateway route propagation).

### Q11. FortiGate interfaces in Azure — what maps to what?
`port1` external (public/untrust subnet, behind ELB), `port2` internal (trust subnet, behind ILB), `port3` HA sync, `port4` HA management (A/P). Each NIC has **IP forwarding enabled** and its own NSG — usually permissive on data NICs because FortiGate enforces policy, restrictive on management.

### Q12. FortiGate vs Azure Firewall — when choose which?
**FortiGate**: existing Fortinet skills/licences, SD-WAN, consistent policy with on-prem, advanced UTM/IPS, FortiManager central management. **Azure Firewall**: PaaS (no patching/HA design), autoscale, native Firewall Policy & IaC, Premium has TLS inspection + IDPS. Trade-off: NVA = more control, more operational effort.

### Q13. How would you troubleshoot "spoke VM can't reach internet through FortiGate"?
1. **Effective routes** on the VM NIC — is 0/0 → NVA?
2. **Effective security rules** — NSG blocking?
3. **Network Watcher → Next hop / IP flow verify / Connection troubleshoot**.
4. ILB **health probe** status — is any backend healthy?
5. FortiGate: `diagnose sniffer packet any 'host x.x.x.x' 4`, `diagnose debug flow`, check policy + SNAT, static route back to spokes via port2 gateway (subnet .1).
6. IP forwarding enabled on NICs?

## Network Security Groups

### Q14. How do NSGs work?
Stateful L3/L4 filters attached to a **subnet and/or NIC**. Rules evaluated by **priority 100–4096** (lower wins); first match stops. Default rules (65000+) allow VNet-to-VNet and LB probes, deny other inbound. Inbound: subnet NSG then NIC NSG; outbound: NIC then subnet. Use **service tags** (Internet, VirtualNetwork, AzureLoadBalancer, Storage.<region>) and **Application Security Groups** to avoid IP lists.

### Q15. Note on "VirtualNetwork" service tag in hub-spoke?
`VirtualNetwork` includes the VNet, **peered VNets** and on-prem prefixes from the gateway — and with UDRs, also prefixes in route tables. So the default `AllowVnetInBound` is broad; in a zero-trust design add explicit deny rules above it.

### Q16. NSG flow logs vs VNet flow logs?
NSG flow logs are being retired (no new ones since mid-2025; full retirement Sept 2027). **VNet flow logs** are the successor — capture at VNet/subnet/NIC level, work with encryption and AVNM rules, analysed with **Traffic Analytics** in Log Analytics.

## Azure Bastion

### Q17. What is Azure Bastion and why use it?
Managed PaaS jump host giving RDP/SSH over **TLS 443 from the portal or native client**, so VMs need **no public IPs** and no open 22/3389 to the internet. Deploy in hub `AzureBastionSubnet` (/26+); reaches VMs in **peered** spokes. Standard/Premium add native client, IP-based connect, shareable links, scaling; Premium adds session recording and private-only.

### Q18. Bastion gotchas?
- Don't apply a 0/0 UDR to AzureBastionSubnet — not supported.
- If you put an NSG on AzureBastionSubnet it must allow: inbound 443 from Internet, inbound 443 from GatewayManager, inbound 8080/5701 VirtualNetwork (data plane), outbound 22/3389 to VirtualNetwork, outbound 443 AzureCloud, outbound 80 Internet (cert validation).
- Target VM NSG must allow 22/3389 **from AzureBastionSubnet**.

## Hybrid connectivity

### Q19. Site-to-site VPN vs ExpressRoute?
VPN: IPsec over internet, quick, cheap, up to a few Gbps per gateway, encryption built in. ExpressRoute: private circuit via provider, predictable latency, up to 100 Gbps (Direct), **not encrypted by default** (use MACsec on Direct or IPsec over ER). Common: ER primary + VPN failover.

### Q20. Active-active VPN gateway + BGP — why?
Two gateway instances with two public IPs, two tunnels to on-prem (ideally two FortiGate/CPE devices) → full mesh. **BGP** advertises routes dynamically and fails over automatically; static routes don't. Set APIPA/BGP peer IPs and ASNs (Azure default 65515).

### Q21. How do you configure FortiGate on-prem to Azure VPN gateway?
Phase1: IKEv2, Azure public IP as remote GW, PSK, AES256/SHA256, DH group matching the Azure IPsec policy. Phase2: local/remote selectors (or 0/0 with route-based). Static route or BGP neighbour to the Azure BGP peer IP over the tunnel interface. Firewall policy both directions. Verify with `diagnose vpn ike gateway list` and `get vpn ipsec tunnel summary`.

### Q22. How is DNS handled in hub-spoke?
**Private DNS zones** (e.g. `privatelink.blob.core.windows.net`) linked to the hub (and spokes or via resolver). **Azure DNS Private Resolver** in the hub: inbound endpoint for on-prem → Azure lookups, outbound endpoint + forwarding ruleset for Azure → on-prem domains. Spokes use custom DNS pointing to the resolver/FortiGate DNS proxy.

### Q23. What's Azure Virtual Network Manager (AVNM)?
Central service to create **hub-spoke or mesh connectivity configurations** and **security admin rules** (evaluated *before* NSGs, cannot be overridden by app teams) across subscriptions, using network groups with dynamic membership via Azure Policy.

### Q24. Virtual WAN vs custom hub-spoke?
vWAN = Microsoft-managed hub with transitive routing, any-to-any, built-in VPN/ER/P2S, and supports integrated NVAs (FortiGate is a supported vWAN NVA / SaaS). Custom hub = full control over UDRs and NVA design, cheaper at small scale. Choose vWAN for many branches/regions; custom for tight control.
