# 10 — STAR Stories (Situation · Task · Action · Result)

Fill in exact numbers before the call. Keep each story under 2 minutes. Don't name clients.

## Story 1 — Securing public access to a data platform behind load balancers
- **S**: A big-data platform console on OCI had to be reachable by external teams without exposing nodes directly.
- **T**: Design secure access through the hub network and firewall team's controls.
- **A**: Placed public LB in the hub with backend to a private ALB; restricted security lists/NSGs to specific source ranges; TLS at the LB; coordinated firewall rules with the network team; documented the path.
- **R**: Console reachable only from approved sources, no public IPs on nodes, passed security review.
- **Azure/GCP mapping**: AppGW WAF in hub → private backends via FortiGate; GCP external ALB + Cloud Armor → internal backends in Shared VPC.

## Story 2 — Observability stack + AI health agent on Kubernetes
- **S**: Clusters had limited visibility; issues found by users first.
- **T**: Build metrics/logs/alerting and faster root-cause analysis.
- **A**: Deployed kube-prometheus-stack, Loki and Grafana Alloy via Helm/GitOps; built a CronJob-based health agent that collects cluster signals and produces an AI-generated root-cause summary, with human-approved remediation.
- **R**: Earlier detection, faster triage (quantify: MTTR before/after).
- **Mapping**: Azure Monitor + Container Insights + Managed Prometheus/Grafana; GCP Cloud Monitoring/Managed Prometheus + Cloud Logging.

## Story 3 — FortiGate & hybrid connectivity (network engineering background)
- **S**: Sites needed resilient connectivity to central services.
- **T**: Configure IPsec VPN tunnels, VRFs and firewall policies on FortiGate.
- **A**: Built route-based IPsec tunnels with redundant paths, VRF separation, policy-based access, monitoring of tunnel health.
- **R**: Stable hybrid links with failover; quantify uptime.
- **Mapping**: exactly the skills needed for FortiGate NVA in Azure hub + active-active VPN gateway with BGP + GCP HA VPN.

## Story 4 — IaC + CI/CD with security gates
- **S**: Manual infra changes and inconsistent deployments.
- **T**: Standardize on Terraform and pipelines with security checks.
- **A**: Terraform modules, remote state, pipelines with SonarQube, OWASP Dependency-Check, Conftest policies and Trivy scanning; GitOps with Argo CD for Kubernetes.
- **R**: Repeatable, reviewed changes; vulnerabilities caught pre-deploy.
- **Mapping**: Azure DevOps Plan → Approval → Apply with Checkov/Conftest and WIF service connections.

## Story 5 — Secrets & compliance
- **S**: Workloads needed secrets management and compliance controls (mTLS, PCI DSS-style requirements).
- **T**: Remove plaintext secrets and enforce identity-based access.
- **A**: Introduced OpenBao/Vault-style secret store, SOPS-encrypted Git secrets, Keycloak/Entra ID for SSO, mTLS between services.
- **R**: No secrets in repos, auditable access.
- **Mapping**: Key Vault (RBAC, private endpoint, purge protection) / Cloud KMS + Secret Manager, CMEK, VPC-SC.

## Story 6 — Incident / recovery
- **S**: Lost SSH access to a production cloud instance.
- **T**: Recover without rebuilding.
- **A**: Used console connection / boot volume attach method to reset keys; documented a runbook.
- **R**: Restored access with no data loss; runbook reused by team.
- **Mapping**: Azure serial console / VMAccess extension / Run Command; GCP serial console / OS Login.

## Behavioural quick answers
- **Conflict**: disagreed on opening a firewall rule broadly → proposed narrower rule + temporary exception with expiry → agreed.
- **Failure**: an apply caused downtime → introduced plan review + approval gates + `prevent_destroy`.
- **Learning new tech fast**: certifications + hands-on repos (GitHub Project-01…14).
- **Why this role**: want to go deeper on Azure + GCP at enterprise scale; hub-spoke + FortiGate + Terraform is my core skill set.
