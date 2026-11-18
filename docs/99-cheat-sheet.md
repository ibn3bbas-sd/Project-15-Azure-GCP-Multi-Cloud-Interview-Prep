# 99 — One-Page Cheat Sheet

## Azure numbers & names
| Item | Value |
|---|---|
| NSG priority | 100–4096, lower first; defaults 65000+ |
| Route precedence (same prefix) | UDR > BGP > System; longest prefix first |
| AzureBastionSubnet | exact name, /26 min |
| GatewaySubnet | exact name, /27+ recommended |
| AppGW v2 NSG | allow GatewayManager 65200–65535 inbound |
| ILB HA ports | Standard internal LB, protocol All, port 0 |
| Azure VPN BGP ASN | 65515 default |
| Key Vault soft delete | 7–90 days, purge protection irreversible |
| Mgmt group depth | 6 levels below root |
| Activity log retention | 90 days (export for more) |
| Agent | AMA + DCR (MMA retired) |
| Flow logs | VNet flow logs (NSG flow logs retiring) |

## Peering flags
Hub: **Allow gateway transit** · Spoke: **Use remote gateways** · Both: **Allow forwarded traffic** (NVA) · Spoke RT: **Propagate gateway routes = No** · NVA NIC: **IP forwarding = on**

## GCP numbers & names
| Item | Value |
|---|---|
| VPC scope | Global; subnets regional |
| Firewall priority | 0–65535, lower first; implied deny ingress / allow egress |
| Shared VPC roles | `compute.xpnAdmin`, `compute.networkUser` (subnet-level) |
| Cloud NAT | regional, on Cloud Router, outbound only |
| HA VPN SLA | 99.99% with 2 tunnels + BGP |
| restricted.googleapis.com | 199.36.153.4/30 (VPC-SC) |
| private.googleapis.com | 199.36.153.8/30 |
| `_Required` log bucket | 400 days, fixed |
| `_Default` log bucket | 30 days, configurable |
| KMS destroy | scheduled, default 30 days |
| Riyadh-adjacent region | `me-central2` (Dammam) |

## WIF in one breath
External OIDC token → **pool/provider** (issuer, audience) → **attribute mapping + condition** → STS token → **impersonate SA** (`workloadIdentityUser`) → no keys.

## VPC-SC in one breath
Perimeter around projects + restricted APIs; access levels + ingress/egress rules; **dry-run first**; protects against exfiltration even with valid creds.

## Terraform pipeline in one breath
PR: fmt · validate · tflint · Checkov · plan → comment. Main: plan -out → artifact → **Environment approval** → apply **saved plan**. OIDC service connection. Remote state with locking. Scheduled `plan -detailed-exitcode` for drift (exit 2 = drift).

## Azure ↔ GCP ↔ OCI
| Azure | GCP | OCI |
|---|---|---|
| Management group / Subscription / RG | Folder / Project | Compartment |
| VNet (regional) | VPC (global) | VCN |
| NSG / ASG | Firewall rules / policies, tags/SAs | Security list / NSG |
| UDR | Custom static route | Route table |
| VPN GW / ExpressRoute | HA VPN / Interconnect + Cloud Router | DRG / FastConnect |
| NAT Gateway | Cloud NAT | NAT Gateway |
| App Gateway + WAF | External ALB + Cloud Armor | LB + WAF |
| Private Endpoint | Private Service Connect | Private Endpoint |
| Entra ID / RBAC | Cloud Identity / IAM | IAM domains / policies |
| Azure Policy | Org Policy | Security Zones / quotas |
| Key Vault | Cloud KMS + Secret Manager | Vault |
| Defender for Cloud | Security Command Center | Cloud Guard |
| Azure Monitor / Log Analytics | Cloud Monitoring / Logging | Monitoring / Logging |
| AKS | GKE | OKE |

## Say this when stuck
"I haven't run that exact feature in production; here's how I'd approach it, and here's the equivalent I've operated…"
