# 00 — Interview Game Plan (30-minute technical round)

## Time budget

| Minute | What happens | Your goal |
|---|---|---|
| 0–3 | Intro | 60-second pitch, calm, specific |
| 3–20 | Technical deep dive | Answer → example → trade-off |
| 20–27 | Scenario / design | Draw it, state assumptions, security first |
| 27–30 | Your questions | 2 sharp questions |

## 60-second pitch (rehearse out loud)

> "I'm a Senior DevOps/Cloud Engineer with a network-engineering background. Today I run
> production infrastructure for government workloads: Kubernetes clusters, load balancers and
> network security, data platforms, observability, and CI/CD — all as code with Terraform and
> pipelines. Before cloud I configured FortiGate firewalls, IPsec VPNs and VRFs, so hub-and-spoke
> with an NVA is familiar ground for me. On Azure I hold the DevOps Engineer Expert, Network
> Engineer and Administrator certifications; on GCP I've worked with GKE and hold Cloud Digital
> Leader; and I'm OCI Multicloud Architect certified. I like building secure landing zones where
> networking, identity and pipelines are designed together, not bolted on."

## Answer formula (use every time)

1. **Direct answer** in one sentence.
2. **How it works** in 2–3 sentences.
3. **Real example** — "In my environment I…" (map from OCI/OKE/FortiGate when needed).
4. **Trade-off or gotcha** — this is what makes the answer senior.

## Bridging phrases (OCI → Azure/GCP)

| You did (OCI / on-prem) | Say it in Azure terms | Say it in GCP terms |
|---|---|---|
| VCN, subnets, DRG | VNet, subnets, VPN/ER gateway | VPC, subnets, Cloud VPN/Interconnect |
| Route tables to firewall | UDR, next hop = NVA ILB IP | Custom static route, next hop = ILB |
| Security lists / NSGs | NSG + ASG | VPC firewall rules / policies, tags/SAs |
| OCI LB / Network LB | App Gateway / Azure LB | External/Internal ALB / NLB |
| Compartments + IAM policies | Mgmt groups / subs / RGs + RBAC | Folders / projects + IAM |
| OCI Vault | Key Vault | Cloud KMS / Secret Manager |
| Cloud Guard | Defender for Cloud | Security Command Center |
| OKE | AKS | GKE |
| FortiGate HA pair on-prem | FortiGate A/P behind ILB HA ports | FortiGate behind internal passthrough NLB |

## If you don't know

> "I haven't operated that in production. Here's how I'd reason about it…, and here's the
> equivalent I *have* run: …. I'd confirm in the docs before rolling it out."

Never bluff a specific number or SKU.

## Questions to ask them

- "How is the Azure/GCP landing zone structured today — ALZ / Fabric-based, or custom? Who owns the Terraform modules?"
- "Is the FortiGate deployed active-passive or active-active, and how are you handling route symmetry?"
- "What does the path to production look like for an infra change — approvals, drift detection, policy as code?"
- "What's the biggest infrastructure challenge for this team in the next six months?"

## Pre-call checklist

- Teams tested, camera + mic, quiet room, charger, water.
- Notepad / whiteboard tool open (draw.io or paper) for the hub-spoke diagram.
- This repo's `99-cheat-sheet.md` open in a second screen — glance, don't read.
- Join 5 minutes early.
