# 09 — Scenario & Design Questions

Approach for every scenario: **clarify → assumptions → draw → security → operations → trade-offs**.

### S1. Design a secure hub-and-spoke in Azure with FortiGate for 3 workloads plus on-prem connectivity.
- **MG/subs**: Connectivity sub (hub), one sub per workload in Corp LZ; ALZ policies.
- **Hub VNet** 10.0.0.0/16: GatewaySubnet (active-active VPN GW + BGP, or ER), FortiGate A/P with ext Standard LB + int ILB **HA ports**, AzureBastionSubnet, AppGW WAF v2 subnet for published apps, DNS Private Resolver.
- **Spokes** 10.1–10.3/16: peering (hub: allow gateway transit; spokes: use remote gateways, allow forwarded traffic); UDR 0/0 + other spokes → ILB; gateway route propagation off; NSGs per subnet with ASGs.
- **GatewaySubnet UDR**: spoke prefixes → ILB (symmetry).
- **Identity**: Entra ID, PIM for Owner/Network Contributor, managed identities, WIF for pipelines.
- **Secrets**: Key Vault per workload, RBAC, private endpoints, purge protection.
- **Ops**: diagnostic settings → central Log Analytics; FortiGate logs → FortiAnalyzer/Sentinel; Defender CSPM + plans; Connection Monitor.
- **IaC**: Terraform layered states (connectivity / each spoke), ADO Plan→Approval→Apply.
- **Trade-offs**: A/P simpler + session sync vs A/A throughput; FortiGate vs Azure Firewall; vWAN if scaling to many regions.

### S2. Spoke-A VMs can reach the internet but not Spoke-B. What do you check?
Peerings both to hub ✔? **Allow forwarded traffic** enabled on hub↔spoke peerings? UDR in Spoke-A has route for Spoke-B prefix → ILB (and Spoke-B for Spoke-A — **symmetry**)? FortiGate has static route to both spokes via port2 and a policy port2→port2 (intra-zone) allowing it? NSGs in Spoke-B allow source Spoke-A? Use Network Watcher **next hop** and FortiGate `diagnose debug flow`.

### S3. After adding ExpressRoute, the firewall stops seeing on-prem traffic to spokes. Why?
The ER gateway learns spoke routes via peering and on-prem now reaches spokes **directly**, and spokes learn on-prem prefixes via BGP (more specific than 0/0 UDR) → bypass. Fix: GatewaySubnet UDR (spokes → ILB), spoke route tables with **gateway propagation disabled** and explicit on-prem routes → ILB.

### S4. Publish an internal web app to the internet securely.
Option A: Internet → **AppGW WAF v2 (public frontend, Prevention mode, DRS 2.1)** → backend in spoke over HTTPS (end-to-end TLS, cert from Key Vault via UAMI), UDR on AppGW subnet for backend prefixes → FortiGate if inspection needed. Option B: Front Door Premium + WAF + Private Link origin. DNS, DDoS Network Protection on hub PIPs, logging to workspace, alert on WAF blocks.

### S5. Design GCP networking for 2 environments with on-prem connectivity and data-exfiltration protection.
Folders prod/nonprod; **Shared VPC host project per env**; custom-mode VPC, regional subnets (me-central2 + DR region) with GKE secondary ranges; **HA VPN** (or Interconnect) + Cloud Router BGP, global dynamic routing; **Cloud NAT** per region with static IPs for partner allow-lists; hierarchical firewall policy at org (deny-by-default baseline) + network firewall policy per VPC using secure tags; **PGA + restricted.googleapis.com** DNS zone; **VPC-SC perimeter** per env (dry-run first); org policies (no external IPs, no SA keys, resource locations); centralized logging sinks; SCC Premium. All via Fabric/foundation Terraform with WIF-based pipelines.

### S6. A developer's Terraform apply failed with "state locked". What now?
Check who holds the lock (lock info shows ID, who, operation). Confirm no pipeline is running. If a crashed run left it, `terraform force-unlock <LOCK_ID>` — only after confirming. Root-cause: why did a developer apply locally? Move applies to pipeline only; restrict state access to pipeline identity.

### S7. Someone changed an NSG in the portal; Terraform wants to revert it in prod. What do you do?
Don't blindly apply. Find out why (Activity log: caller, time). If the change was a valid hotfix, codify it in a PR so plan is clean; if not, let Terraform revert after approval. Prevent recurrence: read-only portal for humans in prod, PIM for break-glass, scheduled drift detection, Azure Policy deny for risky rules.

### S8. Bring a GCP project under VPC-SC without breaking the CI/CD pipeline running in Azure DevOps.
Dry-run perimeter; observe violations from the ADO deploy SA; add **ingress rule**: identity = deploy SA (via WIF), source = access level with ADO agent egress IPs (self-hosted agents with static NAT), services = specific APIs/methods; enforce; test pipeline; alert on violations.

### S9. Rotate a secret used by 20 apps without downtime.
Store in Key Vault/Secret Manager; apps read via managed identity at runtime (not baked into config); create new version → dual-validity window (old + new accepted at the backend) → apps pick up new version (refresh interval / restart) → revoke old. Automate with Event Grid / Pub/Sub expiry notifications.

### S10. Cost of the hub doubled this month. Investigate.
Cost Management by resource/meter: FortiGate VM scaling? Licence (PAYG vs BYOL)? **VNet peering data transfer** spike (new chatty spoke-to-spoke traffic through hub)? Log Analytics ingestion jump (new diagnostic setting or debug logging on FortiGate)? NAT/egress? Fix root cause, add budget alerts and anomaly detection.

### S11. Migrate a 3-tier app from on-prem (behind FortiGate) to Azure with minimal downtime.
Assess dependencies, build spoke via vending pipeline, extend network via VPN/ER, replicate VMs with Azure Migrate, DB via DMS online, map FortiGate policies to hub FortiGate (same platform simplifies), test migration in isolated VNet, cutover with low DNS TTL, rollback plan, then optimize.

### S12. How would you make the hub FortiGate itself managed as code?
FortiGate **Terraform provider (fortios)** or FortiManager with Terraform/Ansible; policy objects in Git; pipeline with plan + approval; config backups; separate change windows from Azure infra changes.
