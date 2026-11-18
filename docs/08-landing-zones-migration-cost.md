# 08 — Landing Zones, Migration & Cost Optimization

## Landing zones

### Q1. What is a landing zone?
A pre-built, governed cloud environment — identity, network topology, security baselines, logging, policy, billing structure and subscription/project vending — ready for workloads to land on safely and repeatably. Built as code.

### Q2. Azure Landing Zone (ALZ) management group hierarchy?
```
Tenant Root
└── <org>
    ├── Platform
    │   ├── Identity      (DCs / Entra DS)
    │   ├── Management    (Log Analytics, Automation, Sentinel)
    │   └── Connectivity  (hub VNet / FortiGate / vWAN, DNS, ER/VPN)
    ├── Landing Zones
    │   ├── Corp    (private, connected to hub)
    │   └── Online  (internet-facing)
    ├── Sandbox
    └── Decommissioned
```
Policies assigned at each MG (e.g. Corp denies public IPs). Implement with **ALZ Terraform (AVM-based pattern modules)** or ALZ Bicep / portal accelerator.

### Q3. Subscription vending?
Automated creation of a new landing-zone subscription via pipeline: create subscription (EA/MCA billing scope), place in MG, create spoke VNet + peering to hub + UDR, RBAC for the app team, budget, Defender, diagnostic settings. Terraform module + ADO pipeline triggered by a request form.

### Q4. GCP landing zone (foundation) structure?
Google **terraform-example-foundation** / **Cloud Foundation Fabric FAST** stages: 0-bootstrap (seed project, state bucket, CI/CD SAs with WIF) → 1-org (org policies, logging sinks, SCC, KMS) → 2-environments (folders dev/nonprod/prod) → 3-networks (Shared VPC hub-spoke or NCC, DNS, VPC-SC, HA VPN/Interconnect) → 4-projects (project factory, service projects attached) → 5-app-infra.

### Q5. Multi-cloud design principles between Azure and GCP?
Single corporate IdP (Entra ID) federated to GCP (Cloud Identity SSO / Workforce Identity Federation); non-overlapping IP plan across Azure, GCP, OCI and on-prem; consistent tagging/labels; central SIEM; one IaC toolchain (Terraform) and one pipeline platform; cloud-to-cloud connectivity via VPN between Azure VPN GW and GCP HA VPN (BGP), or partner interconnect / Cross-Cloud Interconnect; consistent security baseline (CIS benchmarks) per cloud.

### Q6. How do you connect Azure and GCP privately?
**HA VPN (GCP) ↔ active-active VPN gateway (Azure)** with 4 tunnels and BGP (Cloud Router ASN vs Azure ASN 65515 or custom), APIPA ranges on Azure (169.254.21.x / 169.254.22.x) matching GCP link-local. Higher bandwidth: Cross-Cloud Interconnect or colocation (Equinix) with ExpressRoute + Partner Interconnect. Or terminate both on FortiGates for consistent policy.

## Migration

### Q7. Migration strategies (the R's)?
Rehost (lift & shift), Replatform (e.g. VM SQL → Azure SQL MI / Cloud SQL), Refactor/Re-architect (containers, PaaS), Repurchase (SaaS), Retire, Retain. Pick per app based on business value, complexity, timeline.

### Q8. How would you run a VM migration to Azure?
**Assess** (Azure Migrate discovery appliance: dependencies, sizing, cost) → **plan waves** by dependency groups → **landing zone ready** (network, identity, policy) → **replicate** (Azure Migrate server migration, agentless for VMware) → **test migration** in isolated VNet → **cutover** (DNS, firewall rules, final sync) → **optimize** (rightsize, reservations) → decommission source. GCP equivalent: **Migrate to Virtual Machines**.

### Q9. Database migration?
Azure Database Migration Service / GCP Database Migration Service (online with CDC for minimal downtime). Validate row counts and app tests, plan rollback, coordinate cutover window.

### Q10. Biggest migration risks?
Undiscovered dependencies, IP/DNS hardcoding, licensing, latency to on-prem dependencies, firewall rules not migrated (FortiGate policy mapping), data residency, missing rollback plan.

## Cost & performance

### Q11. Azure cost levers?
Rightsize (Advisor), **Reservations** (1/3-yr for steady VMs/DBs), **Savings Plans for compute** (flexible), **Azure Hybrid Benefit** (Windows/SQL licences), Spot VMs for interruptible work, autoscale (VMSS/AKS), auto-shutdown for dev, storage tiering/lifecycle, Log Analytics tuning, delete orphaned disks/PIPs/NICs, budgets + alerts per subscription, tags for showback.

### Q12. GCP cost levers?
**Sustained use discounts** (automatic for N1/N2 etc.), **Committed use discounts** (resource-based or spend-based flexible), Spot VMs, rightsizing **Recommender**, custom machine types, autoscaling MIGs/GKE, storage classes + lifecycle, Cloud NAT/egress awareness, BigQuery slot/reservation strategy, budgets + Pub/Sub alerts, billing export to BigQuery for analysis.

### Q13. Network cost gotchas?
Azure: VNet peering charged per GB in/out (global peering more), NVA throughput needs bigger VMs, NAT Gateway per-GB, ER egress. GCP: egress between regions/internet, Cloud NAT processing, inter-zone traffic. Design: keep chatty services in same region/zone; centralize inspection only where needed.

### Q14. Performance tuning examples?
Accelerated networking on NVAs and VMs; right FortiGate VM size for throughput/IPS; proximity placement groups for latency; Premium SSD v2 / Ultra for IOPS; AppGW min instances; GCP: gVNIC + Tier_1 networking, regional MIGs, Cloud CDN.

### Q15. FinOps governance?
Tagging policy enforced (Azure Policy / org policy for labels via CI checks), budgets per subscription/project with owners, monthly cost review, anomaly alerts (Cost Management anomaly detection / GCP budget alerts), unit economics per app.
