# 03 — Azure Identity & Governance (Entra ID, RBAC, Policy, Key Vault, Defender)

## Entra ID

### Q1. Entra ID tenant vs subscription vs management group?
**Tenant** = identity boundary (users, groups, apps). **Subscription** = billing + resource boundary, trusts exactly one tenant. **Management groups** = hierarchy above subscriptions (up to 6 levels below root) for applying RBAC and Policy at scale.

### Q2. Service principal vs managed identity?
Both are app identities in Entra ID. **Service principal** = identity of an app registration; you manage secrets/certs (or federated credentials). **Managed identity** = service principal managed by Azure, no secrets, only usable from Azure resources. **System-assigned**: lifecycle tied to resource. **User-assigned**: standalone, shareable, survives resource recreation — preferred for IaC.

### Q3. What is workload identity federation in Azure?
Trust an external OIDC issuer (Azure DevOps, GitHub Actions, GKE, another cloud) with a **federated credential** on an app registration or user-assigned identity: issuer + subject (+ audience). The workload exchanges its OIDC token for an Entra token — **no stored secrets**. Azure DevOps "Workload identity federation" service connections use this.

### Q4. Conditional Access?
Policy engine: **if** (users/groups, apps, location, device platform, sign-in risk) **then** (grant with MFA / compliant device / block, session controls). Use for admins: require MFA + compliant device; block legacy auth; named locations. Start in **report-only**. Keep break-glass accounts excluded.

### Q5. What is PIM?
**Privileged Identity Management** — just-in-time, time-bound, approval-based **eligible** role assignments (Entra roles and Azure RBAC) with MFA and justification, plus access reviews and audit. Reduces standing Owner/Contributor.

## RBAC

### Q6. How does Azure RBAC work?
Role assignment = **security principal + role definition + scope**. Scope: management group → subscription → resource group → resource; inherited downward. Permissions are **additive**; **deny assignments** (from Blueprints/managed apps/Deployment Stacks) override.

### Q7. Key built-in roles?
**Owner** (all + grant access), **Contributor** (all except access mgmt), **Reader**, **User Access Administrator** (manage access only), **Role Based Access Control Administrator** (can be constrained by conditions on which roles it assigns). Network: **Network Contributor**. Key Vault data plane: **Key Vault Administrator / Secrets Officer / Secrets User / Crypto User / Certificates Officer**.

### Q8. Control plane vs data plane?
Control plane = ARM (`management.azure.com`) — creating a Key Vault or storage account. Data plane = reading a secret or a blob. `Owner` on a Key Vault doesn't let you read secrets under RBAC permission model; you need a data role (`Key Vault Secrets User`).

### Q9. How do you write a custom role?
JSON with `Actions`, `NotActions`, `DataActions`, `NotDataActions`, `AssignableScopes`. Example: VM operator who can start/stop/restart but not delete:
```json
{
  "Name": "VM Operator",
  "Actions": [
    "Microsoft.Compute/virtualMachines/read",
    "Microsoft.Compute/virtualMachines/start/action",
    "Microsoft.Compute/virtualMachines/restart/action",
    "Microsoft.Compute/virtualMachines/deallocate/action"
  ],
  "AssignableScopes": ["/subscriptions/<sub-id>"]
}
```

### Q10. RBAC vs Azure Policy?
RBAC = **who** can do what. Policy = **what** is allowed regardless of who (e.g. only allowed regions, require tags, deny public IPs). Effects: `Deny`, `Audit`, `Append`, `Modify`, `DeployIfNotExists`, `AuditIfNotExists`, `Disabled`, `DenyAction`. Group policies in **initiatives**; assign at MG; remediation tasks for DINE/Modify (needs a managed identity).

### Q11. Example policies for a hub-spoke landing zone?
Deny public IPs on NICs in spokes; deny subnets without NSG; deny VNet peering to non-hub VNets; require private endpoints / deny public network access on PaaS; allowed locations (e.g. Saudi/Qatar/UAE region); require tags (`env`, `owner`, `costCenter`); deploy diagnostic settings to central Log Analytics (DINE); enable Defender plans.

## Key Vault

### Q12. Key Vault RBAC vs access policies?
**Azure RBAC permission model** (recommended): uniform with the rest of Azure, granular at vault/secret scope, PIM-able. **Access policies** (legacy): vault-level only, managed by anyone with Contributor — a privilege-escalation risk. Default for new vaults is RBAC.

### Q13. Soft delete and purge protection?
**Soft delete** is mandatory (7–90 days retention) — deleted vaults/secrets are recoverable. **Purge protection** prevents permanent deletion until retention ends — even by admins. Required for CMEK scenarios (storage/SQL/disk encryption keys). Cannot be turned off once enabled.

### Q14. How do you secure Key Vault network access?
Disable public network access, use a **private endpoint** + `privatelink.vaultcore.azure.net` private DNS zone, allow **trusted Microsoft services** if needed, RBAC least privilege, diagnostic logs (`AuditEvent`) to Log Analytics, alerts on unusual access.

### Q15. Keys vs secrets vs certificates; Standard vs Premium vs Managed HSM?
**Secrets**: arbitrary strings. **Keys**: RSA/EC for crypto operations (never exported). **Certificates**: X.509 with lifecycle, auto-renew with integrated CAs. **Standard**: software keys. **Premium**: HSM-backed keys (FIPS 140 Level 3). **Managed HSM**: single-tenant HSM pool, local RBAC, highest compliance.

### Q16. How do apps consume secrets without secrets?
Managed identity → Key Vault (SDK or **Key Vault references** in App Service / Functions app settings; **Secrets Store CSI driver** in AKS with workload identity). Rotate with Event Grid `SecretNearExpiry` → Function.

## Defender for Cloud

### Q17. What is Microsoft Defender for Cloud?
CNAPP: **CSPM** (posture — secure score, recommendations based on Microsoft Cloud Security Benchmark, regulatory compliance dashboards, attack-path analysis in Defender CSPM) + **CWP** plans (Defender for Servers, Containers, Storage, SQL, Key Vault, App Service, Resource Manager, DNS/APIs). Multi-cloud: connects **GCP** and AWS accounts too.

### Q18. Foundational CSPM vs Defender CSPM?
Foundational (free): secure score, recommendations, asset inventory, MCSB. Defender CSPM (paid): attack-path analysis, cloud security explorer, agentless scanning, data-aware posture, governance rules, extra compliance standards.

### Q19. How do you operationalize Defender alerts?
Continuous export to Log Analytics / Event Hub → **Microsoft Sentinel** analytics rules and playbooks (Logic Apps); workflow automation for high-severity alerts → Teams/ITSM; governance rules assigning owners and due dates to recommendations.

### Q20. How would you enforce Defender plans everywhere?
Built-in policy initiative / `DeployIfNotExists` assignments at the landing-zone management group that enable plans on every subscription; in Terraform `azurerm_security_center_subscription_pricing` per plan.
