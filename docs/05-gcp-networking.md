# 05 — GCP Networking & Perimeter Security

```
Organization
└── Folder: prod
    ├── Host project (prod-net-host) ── Shared VPC "prod-vpc" (global)
    │     subnets: me-central2/app 10.10.0.0/20, me-central2/data 10.10.16.0/20
    │     Cloud Router + Cloud NAT (per region), HA VPN / Interconnect to on-prem
    ├── Service project: app-prod   (VMs/GKE attached to app subnet)
    └── Service project: data-prod  (attached to data subnet)
VPC Service Controls perimeter: [app-prod, data-prod] protecting storage/bigquery APIs
```

## VPC basics

### Q1. How is a GCP VPC different from an Azure VNet?
A GCP VPC is **global**; **subnets are regional**. One VPC can span regions without peering. Routes and firewall rules are VPC-wide. Azure VNets are regional and need peering across regions.

### Q2. Auto vs custom mode VPC?
Auto mode creates a /20 subnet in every region from 10.128.0.0/9 — overlap risk, not for enterprise. Always **custom mode** with planned IPAM; enforce with org policy `compute.skipDefaultNetworkCreation`.

### Q3. Firewall rules vs firewall policies?
**VPC firewall rules**: per-VPC, stateful, priority 0–65535, targets by network tags or **service accounts** (preferred — tags can be changed by anyone with instance edit). **Hierarchical firewall policies**: at org/folder, evaluated first, can `goto_next`. **Network firewall policies** (global/regional): support secure tags (IAM-governed), FQDN/geo objects, threat intelligence, and Cloud NGFW Enterprise (IPS).

### Q4. Implied rules?
Every VPC has implied **allow all egress** and **deny all ingress** (priority 65535). Default network also ships permissive rules (allow-internal, ssh, rdp, icmp) — another reason to avoid it.

## Shared VPC

### Q5. What is Shared VPC?
One **host project** owns the VPC; **service projects** attach and deploy resources into its subnets. Network team keeps central control of subnets, routes, firewall, NAT, hybrid connectivity; app teams own their projects/billing/IAM. Equivalent to Azure hub with central network ownership — but resources sit *in* the shared network rather than peering.

### Q6. Which roles are involved?
- **Shared VPC Admin** (`roles/compute.xpnAdmin`) at org/folder — enables host projects and attaches service projects.
- **Network User** (`roles/compute.networkUser`) — granted to service-project admins/service accounts on the **host project** (all subnets) or **specific subnets** (least privilege).
- Service project robot accounts need networkUser too: e.g. GKE's `service-<num>@container-engine-robot`, Google APIs SA `<num>@cloudservices`, plus `roles/container.hostServiceAgentUser` for GKE.
- **Network Admin / Security Admin** in host project for network/firewall management.

### Q7. Shared VPC vs VPC Network Peering?
Shared VPC = same network, central admin, within one org. Peering = two separate VPCs exchanging routes, **non-transitive**, each side keeps its own admin, works across orgs, limits on peering groups. Hub-spoke on GCP: Shared VPC per environment + **Network Connectivity Center** (VPC spokes) for transitive connectivity, or peering/VPN to a hub VPC with an NVA.

### Q8. How does GKE work in Shared VPC?
Create subnet with **secondary ranges** for Pods and Services in the host project; grant robots networkUser + hostServiceAgentUser; create a VPC-native cluster in the service project referencing host subnet and secondary range names. Firewall rules for control plane → nodes are managed in the host project.

## Cloud Router, Cloud NAT, hybrid

### Q9. What is Cloud Router?
A managed **BGP speaker** (not a data-plane router) that exchanges routes dynamically for **HA VPN, Cloud Interconnect** and Router appliance. VPC **dynamic routing mode**: *regional* (learned routes only in router's region) or *global* (to all regions). Supports custom advertisements (e.g. advertise `199.36.153.4/30` for restricted Google APIs to on-prem).

### Q10. HA VPN?
Two interfaces, two external IPs, **99.99% SLA** when configured with 2 tunnels to peer device(s) + BGP via Cloud Router. Classic VPN (single interface, static routing) is legacy. With FortiGate: two IPsec tunnels, IKEv2, BGP over tunnel interfaces with link-local 169.254.x.x addresses.

### Q11. What is Cloud NAT?
Managed, **software-defined** outbound NAT (no NAT VM, no chokepoint). Configured **on a Cloud Router**, **regional**, per subnet/range selection. Gives private VMs/GKE nodes egress to internet; **no inbound** connections. Options: auto vs manual (static) NAT IPs — manual for allow-listing by partners; static vs **dynamic port allocation**; endpoint-independent mapping; logging (translations/errors). Private NAT for overlapping networks via NCC.

### Q12. Cloud NAT troubleshooting — "connections timing out"?
Check NAT logs for `OUT_OF_RESOURCES` / dropped due to port exhaustion → raise **min ports per VM**, enable **dynamic port allocation**, add NAT IPs, reduce TCP TIME_WAIT timeout. Also confirm the subnet is in NAT config and VM has no external IP (NAT ignores VMs with external IPs).

### Q13. Private Google Access vs Private Service Connect?
**PGA** (subnet flag): VMs without external IPs reach Google APIs via `private.googleapis.com` / `restricted.googleapis.com` VIPs. **PSC**: private endpoint IP inside your VPC for Google APIs (bundle) or for **published services** (yours, partners', Cloud SQL) — similar to Azure Private Endpoint. **Private services access**: VPC peering-based for Cloud SQL/Memorystore (older model).

## VPC Service Controls

### Q14. What problem does VPC-SC solve?
**Data exfiltration** from Google-managed services (Cloud Storage, BigQuery, Secret Manager, etc.) even when **credentials are stolen or IAM is misconfigured**. A **service perimeter** around projects allows API calls only from inside the perimeter or matching access levels/ingress rules. IAM says *who*; VPC-SC says *from where / to where*.

### Q15. Key VPC-SC concepts?
- **Service perimeter**: projects + restricted services.
- **Access levels** (Access Context Manager): IP ranges, device policy, identities.
- **Ingress / egress rules**: precise exceptions (identity + source + service + method + target project).
- **Perimeter bridges**: share between perimeters (prefer ingress/egress rules now).
- **Dry-run mode**: logs violations without enforcing — always start here.
- **Restricted VIP** `restricted.googleapis.com` (199.36.153.4/30) with DNS + route so on-prem/VPC traffic stays on supported services.

### Q16. How do you roll out VPC-SC safely?
1. Inventory API usage (Cloud Audit Logs). 2. Create perimeter in **dry-run**. 3. Watch `VPC_SERVICE_CONTROLS` violation logs, add ingress/egress rules (CI/CD SAs, BI tools, on-prem ranges via access levels). 4. Enforce. 5. Manage perimeter in Terraform (`google_access_context_manager_service_perimeter`) with change review.

### Q17. Common VPC-SC breakages?
CI/CD runner outside the perimeter pushing to GCS/Artifact Registry; Console access from a non-allow-listed IP; cross-project BigQuery jobs; Cloud Build default pool (use private pools inside perimeter); third-party SaaS reading buckets. Error: `Request is prohibited by organization's policy. vpcServiceControlsUniqueIdentifier: …` — search that ID in logs.

### Q18. Load balancing options in GCP?
**Application LB** (L7): global external, regional external, regional/cross-region internal — Cloud Armor WAF on external. **Network LB**: proxy (TCP/SSL) or **passthrough** (regional, preserves client IP). Internal passthrough NLB is used as **next hop** for NVA HA (like Azure ILB HA ports).

### Q19. How would you insert a FortiGate in GCP?
FortiGate VMs with multiple NICs (each NIC in a different VPC — GCP rule), **internal passthrough NLB** as next hop in a custom route `0.0.0.0/0 → ILB` in the internal/trust VPC; external NLB for inbound; Cloud NAT or FortiGate public IP for egress; FGCP A/P with health checks. Remember to remove the default internet route from the trust VPC.
