# 07 — Terraform & Azure DevOps (Plan/Apply pipelines, Git workflows)

## Terraform fundamentals

### Q1. What is Terraform state and why does it matter?
State maps config to real resource IDs and stores attributes for diffing. It can contain **secrets**, so store it remotely, encrypted, access-controlled, with **locking**. Azure: `azurerm` backend in a Storage Account (blob lease lock, use Entra auth `use_azuread_auth = true`, private endpoint, versioning + soft delete). GCP: `gcs` backend (native locking, versioning, CMEK).

### Q2. How do you split state?
By **blast radius and lifecycle**: per environment × per layer (bootstrap → management/governance → connectivity hub → spokes/landing zones → workloads). Never one giant state. Read across with `terraform_remote_state` or, better, data sources / outputs published to a config store.

### Q3. count vs for_each?
`count` indexes by number — removing a middle item shifts and recreates others. `for_each` keys by map/set — stable. Use `for_each` for spokes, subnets, peerings.

### Q4. How do you refactor without destroying?
`moved {}` blocks (rename/move into module), `import {}` blocks (Terraform 1.5+) for brownfield resources with `-generate-config-out`, `removed {}` (1.7+) to forget without destroying, `terraform state mv/rm` as last resort.

### Q5. Module design principles?
Small, composable, opinionated defaults with secure-by-default settings; versioned (Git tags / private registry); inputs validated (`validation` blocks); outputs explicit; no provider blocks inside child modules; examples + tests (`terraform test`, Terratest). Prefer **Azure Verified Modules** and Google **Cloud Foundation Fabric** modules over writing from scratch.

### Q6. Providers & versions?
Pin `required_version` and provider constraints (`~> 4.0`); commit `.terraform.lock.hcl`; upgrade deliberately in a PR with plan review. `azurerm` 4.x requires `subscription_id` in the provider block.

### Q7. Handling secrets in Terraform?
Never in `.tfvars` in Git. Read from Key Vault / Secret Manager at plan time via data sources, or generate (`random_password`) and write directly into the vault; mark variables `sensitive`; use **ephemeral resources/values** (1.10+) where supported so secrets don't land in state; restrict state access.

### Q8. Drift detection?
Scheduled pipeline runs `terraform plan -detailed-exitcode` — exit code **0** no changes, **1** error, **2** changes present → raise alert/ticket. Combine with Azure Policy/Org Policy to prevent manual change, and read-only portal roles in prod.

### Q9. Policy as code for Terraform?
Pre-plan: `terraform fmt -check`, `validate`, **tflint** (with azurerm/google rulesets), **Checkov / Trivy (tfsec)** for misconfig. Post-plan: `terraform show -json plan.out` → **OPA/Conftest** or Sentinel rules (e.g. deny public IP, require tags, deny NSG rule from `*` to 22). Cloud side: Azure Policy / Org Policy as the final backstop. I've used Conftest + Trivy in a DevSecOps pipeline before.

## Azure DevOps pipelines

### Q10. Describe your Plan/Apply pipeline model.
1. **PR validation** (on PR to `main`): fmt, validate, tflint, Checkov, `plan` → post plan summary as PR comment. Branch policy: build must pass + required reviewers (CODEOWNERS-style).
2. **Merge to main** triggers:
   - **Plan stage**: `terraform plan -out=tfplan`, publish `tfplan` + lock file as **pipeline artifact**.
   - **Apply stage**: `deployment` job targeting an ADO **Environment** with **Approvals & checks** (approvers, business hours, exclusive lock), downloads the **exact plan artifact** and runs `terraform apply tfplan`.
3. Promote dev → test → prod as separate stages/environments with separate state and service connections.

### Q11. Why apply a saved plan file?
Guarantees what was reviewed is exactly what gets applied. If state changed since plan, apply of a stale plan fails ("Saved plan is stale") — safe behaviour. The plan file may contain secrets → treat artifact as sensitive, short retention.

### Q12. How does the pipeline authenticate to Azure?
**Azure Resource Manager service connection using Workload Identity Federation** (OIDC) — no client secret to rotate. In the job, `AzureCLI@2` with `addSpnToEnvironment: true` exposes `servicePrincipalId`, `tenantId`, `idToken`; set `ARM_USE_OIDC=true`, `ARM_CLIENT_ID`, `ARM_TENANT_ID`, `ARM_SUBSCRIPTION_ID`, `ARM_OIDC_TOKEN`. Separate service connections per environment, scoped to that subscription/MG with least-privilege roles.

### Q13. And to GCP from Azure DevOps?
Same OIDC idea: ADO token → GCP **Workload Identity Federation** → impersonate a deploy SA. No JSON keys stored in variable groups.

### Q14. Classic vs YAML pipelines; templates?
YAML: versioned with code, reviewable, templates (`extends`, `stages`/`jobs`/`steps` templates) in a central repo with `resources.repositories` — enforce required templates via **Required template** check on environments. Classic release pipelines are legacy.

### Q15. Variable groups and secrets?
Variable groups linked to **Key Vault** (secrets pulled at runtime); mark secrets as secret; pipeline permissions per group; never echo. Prefer OIDC over stored creds altogether.

### Q16. Self-hosted vs Microsoft-hosted agents?
Microsoft-hosted: zero maintenance, public egress — can't reach private endpoints. **Self-hosted / Managed DevOps Pools** in a spoke VNet: reach private state storage, private endpoints, on-prem; pin Terraform/tool versions; ephemeral agents (VMSS/containers) for clean builds.

### Q17. Git workflow you use?
**Trunk-based** with short-lived feature branches → PR → squash merge to `main`; branch policies (min reviewers, linked work item, build validation, comment resolution); semantic version tags for modules; Conventional Commits for changelogs. GitFlow only for products with formal releases.

### Q18. GitLab CI / GitHub Actions / Argo CD → Azure DevOps mapping?
| Concept | GitLab CI | GitHub Actions | Azure DevOps |
|---|---|---|---|
| Pipeline file | `.gitlab-ci.yml` | `.github/workflows/*.yml` | `azure-pipelines.yml` |
| Approval gate | protected environments | environments + reviewers | Environments → Approvals & checks |
| Reusable logic | `include` / components | reusable workflows / actions | templates / `extends` |
| Secrets | CI/CD variables | secrets / OIDC | variable groups / Key Vault / WIF |
| GitOps | Argo CD / Flux (pull) | same | same — ADO builds images, Argo deploys |

### Q19. How do you handle a failed apply in prod?
Stop, don't re-run blindly. Read error; check partial state (`terraform plan` again). Fix forward via PR (preferred) or revert commit → new plan → approval → apply. Use `prevent_destroy` on critical resources (hub VNet, Key Vault, state SA), resource locks (`CanNotDelete`) in Azure.

### Q20. How do you prevent two pipelines from applying at once?
State locking (blob lease / GCS lock) + ADO **Exclusive lock** check on the environment + pipeline `lockBehavior: sequential`.
