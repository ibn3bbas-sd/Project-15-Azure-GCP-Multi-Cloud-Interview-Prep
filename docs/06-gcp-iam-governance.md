# 06 — GCP Identity, Governance & Compliance

## Resource hierarchy & IAM

### Q1. Describe the GCP resource hierarchy.
**Organization** (tied to a Workspace/Cloud Identity domain) → **Folders** (nested, e.g. by BU / environment) → **Projects** (unit of billing, API enablement, quota, isolation) → **Resources**. IAM and Org Policies attach at any level and inherit downward.

### Q2. How do IAM policies inherit?
The effective policy is the **union** of policies on the resource and all ancestors — you can't remove at a lower level what's granted higher. To subtract, use **IAM Deny policies** (evaluated before allow) or don't grant high. So grant broad roles low, and narrow roles high.

### Q3. Basic vs predefined vs custom roles?
**Basic** (Owner/Editor/Viewer) — too broad; avoid in prod. **Predefined** — service-specific (`roles/compute.networkAdmin`). **Custom** — your permission set at org or project level; you maintain it when Google adds permissions.

### Q4. Principals in GCP?
Google accounts, **Google groups** (grant to groups, not users), service accounts, Cloud Identity/Workspace domains, `allUsers`/`allAuthenticatedUsers` (block with org policy), and **principal sets** from workload/workforce identity pools.

### Q5. IAM Conditions?
Attribute-based conditions on role bindings using CEL: time-bound access (`request.time < timestamp(...)`), resource name prefix, resource tags. E.g. grant `roles/storage.objectViewer` only on buckets starting with `logs-`.

### Q6. Service account best practices?
One SA per workload; **no user-managed keys** (enforce `iam.disableServiceAccountKeyCreation`); use **impersonation** (`roles/iam.serviceAccountTokenCreator`) for humans and **Workload Identity Federation** for external workloads; don't use default compute SA with Editor (`iam.automaticIamGrantsForDefaultServiceAccounts`); monitor with IAM Recommender / unused SA insights.

## Organization Policy

### Q7. Org Policy vs IAM?
IAM = who can do what. **Org Policy** = guardrails on *how* resources may be configured, regardless of who (like Azure Policy deny). Inherited down the hierarchy; can be overridden/merged at lower levels unless enforced; supports **dry-run** and **custom constraints** (CEL on resource fields).

### Q8. Org policies you'd set on day one?
- `compute.skipDefaultNetworkCreation` — no default VPC.
- `iam.disableServiceAccountKeyCreation` — no SA keys.
- `iam.allowedPolicyMemberDomains` — only your Cloud Identity customer ID (domain-restricted sharing).
- `compute.vmExternalIpAccess` — deny external IPs (allow-list exceptions).
- `gcp.resourceLocations` — data residency (e.g. `in:me-central2-locations`).
- `storage.uniformBucketLevelAccess`, `storage.publicAccessPrevention`.
- `compute.requireOsLogin`, `sql.restrictPublicIp`, `compute.restrictVpcPeering`, `compute.requireShieldedVm`.
- `iam.automaticIamGrantsForDefaultServiceAccounts` — no Editor for default SAs.

## Workload Identity Federation

### Q9. What is Workload Identity Federation?
Lets **external workloads** (Azure DevOps, GitHub Actions, AWS, Azure VMs, on-prem with OIDC/SAML/X.509) access GCP **without service account keys**. Components: **workload identity pool** → **provider** (issuer URL, allowed audiences) → **attribute mapping** (`google.subject = assertion.sub`, custom attributes) → **attribute condition** (e.g. only a specific repo/branch/org). The external token is exchanged at **STS** for a federated token, then either used directly on resources or to **impersonate a service account** (`roles/iam.workloadIdentityUser`).

### Q10. Walk me through Azure DevOps → GCP with WIF.
1. Pool `ado-pool`; OIDC provider whose issuer matches the `iss` claim of the ADO OIDC token (e.g. `https://vstoken.dev.azure.com/<org-id>`) and the matching audience — decode one token first to confirm.
2. Map `google.subject = assertion.sub` (contains `sc://<org>/<project>/<service-connection>`); condition restricting to that subject.
3. Grant `roles/iam.workloadIdentityUser` on the deploy SA to `principal://iam.googleapis.com/projects/<num>/locations/global/workloadIdentityPools/ado-pool/subject/<sub>`.
4. Pipeline obtains the OIDC token, writes a **credential configuration** file (`gcloud iam workload-identity-pools create-cred-config`), sets `GOOGLE_APPLICATION_CREDENTIALS`, Terraform google provider picks it up.
Same pattern I'd use with GitHub Actions (`google-github-actions/auth`).

### Q11. Workload Identity Federation for GKE?
Kubernetes service accounts act as IAM principals (`principal://…/subject/ns/<ns>/sa/<ksa>`) — grant roles directly or bind KSA to a GSA. No node SA keys, per-pod identity. Equivalent of AKS workload identity / OKE workload identity.

### Q12. Workforce Identity Federation?
Federates **human users** from an external IdP (Entra ID, Okta) via OIDC/SAML into GCP without syncing to Cloud Identity — useful when Entra ID is the corporate IdP. Alternative: Cloud Identity + SAML SSO from Entra ID with user provisioning.

## Cloud KMS

### Q13. Cloud KMS structure?
**Key ring** (location-bound, can't be deleted) → **Crypto key** (purpose: symmetric encrypt, asymmetric sign/decrypt, MAC) → **Key versions** (primary version used for encrypt). Protection levels: **SOFTWARE, HSM** (FIPS 140-2 L3), **EXTERNAL / EXTERNAL_VPC** (Cloud EKM — key held outside Google).

### Q14. What is CMEK and how is it set up?
Customer-managed encryption keys: a Google service (GCS, BigQuery, Compute disks, Cloud SQL, GKE secrets) encrypts with your KMS key. Grant the **service agent** `roles/cloudkms.cryptoKeyEncrypterDecrypter` on the key. Enforce with org policies `gcp.restrictNonCmekServices` and `gcp.restrictCmekCryptoKeyProjects`. Disabling the key = crypto-shred access.

### Q15. Key rotation & destruction?
Automatic rotation period for symmetric keys (e.g. 90 days) — new primary version; old versions still decrypt. Destroy is **scheduled** (default 30 days) and can be cancelled. Separate duties: KMS admins (`cloudkms.admin`) shouldn't have encrypt/decrypt; keep keys in a dedicated security project.

### Q16. Cloud KMS vs Secret Manager?
KMS manages **keys** (data never leaves as plaintext key). Secret Manager stores **secrets** (passwords, API keys) with versions, replication policy, IAM per secret, optional CMEK. Azure Key Vault covers both in one service.

## Security Command Center

### Q17. What is Security Command Center?
GCP's central security & risk platform (like Defender for Cloud): asset inventory, **findings** from Security Health Analytics (misconfigs), **Event Threat Detection** (logs-based threats), Container Threat Detection, VM Threat Detection, Web Security Scanner, vulnerability findings, **attack path / exposure scores** and compliance reports (CIS, PCI DSS, ISO, NIST). Tiers: Standard, Premium, Enterprise (multi-cloud + SecOps).

### Q18. How do you operationalize SCC findings?
Activate at **org level**; **notification configs** → Pub/Sub → Cloud Function / SIEM (Sentinel, Chronicle) / ticketing; **mute rules** for accepted risks; Security Posture service with posture templates; remediate via Terraform/policy rather than console.

## Cloud Logging & audit

### Q19. Cloud Audit Log types?
**Admin Activity** (always on, free, 400 days), **System Event** (always on), **Data Access** (off by default except BigQuery — enable selectively; can be high volume), **Policy Denied** (VPC-SC/org policy denials).

### Q20. How is logging routed?
**Log Router** evaluates **sinks**: `_Required` bucket (audit, 400 days, immutable config) and `_Default` (30 days, configurable). Create **aggregated sinks** at org/folder with `includeChildren` → central log bucket (Log Analytics enabled), BigQuery, Cloud Storage (archive with bucket lock), or Pub/Sub (to Sentinel/Splunk). Use exclusion filters to cut cost.

### Q21. How would you send GCP security logs to Azure Sentinel?
Org aggregated sink → **Pub/Sub topic** → Sentinel **GCP data connectors** (Pub/Sub pull using WIF between Azure and GCP). Gives one SOC view across Azure and GCP.

### Q22. Compliance mapping — how do Azure and GCP line up?
| Control | Azure | GCP |
|---|---|---|
| Guardrails | Azure Policy | Org Policy (+ custom constraints) |
| Posture | Defender for Cloud | Security Command Center |
| Secrets/keys | Key Vault / Managed HSM | Secret Manager / Cloud KMS / EKM |
| Data exfiltration | Private Endpoints + Policy + NSP | VPC Service Controls |
| Audit | Activity log + diagnostic settings | Cloud Audit Logs + Log Router |
| JIT admin | PIM | IAM Conditions + PAM (Privileged Access Manager) |
