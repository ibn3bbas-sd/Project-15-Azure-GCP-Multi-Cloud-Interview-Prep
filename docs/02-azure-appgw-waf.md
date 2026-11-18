# 02 — Azure Application Gateway (WAF, SSL termination, routing)

## Core

### Q1. What is Application Gateway?
A regional **L7 (HTTP/HTTPS) load balancer** with path/host-based routing, SSL termination, end-to-end TLS, rewrites, autoscaling (v2), zone redundancy, and an integrated **WAF**. Lives in a **dedicated subnet** (nothing else in it; /24 recommended for v2 scale).

### Q2. App Gateway components?
**Frontend IP** (public and/or private) → **Listener** (port, protocol, cert, hostname; basic or multi-site) → **Routing rule** (basic or path-based; has a priority in v2) → **Backend setting** (protocol, port, cookie affinity, timeout, host-name override, probe) → **Backend pool** (IPs, FQDNs, VMSS, App Service). Plus **health probes** and **rewrite rule sets**.

### Q3. Application Gateway vs Load Balancer vs Front Door vs Traffic Manager?
| Service | Layer | Scope | Use |
|---|---|---|---|
| Load Balancer | L4 | Regional | TCP/UDP, NVA HA ports |
| Application Gateway | L7 | Regional | Web apps, WAF, private apps |
| Front Door | L7 | Global (edge) | Global web, CDN, WAF at edge |
| Traffic Manager | DNS | Global | DNS-based failover, non-HTTP |

### Q4. How do you do SSL termination and end-to-end TLS?
**Termination**: upload/reference cert on the HTTPS listener; traffic to backend is HTTP — offloads crypto from backends. **End-to-end**: backend setting uses HTTPS; v2 validates the backend cert against well-known CAs or an uploaded **trusted root cert**, and the SNI/host-name must match. Use a **TLS policy** (e.g. `AppGwSslPolicy20220101S`) to enforce TLS 1.2+.

### Q5. How do you integrate certificates with Key Vault?
Give App Gateway a **user-assigned managed identity**, grant it `Key Vault Secrets User` (RBAC model) on the vault, reference the cert's **secret ID** (versionless for auto-rotation — AppGW polls every 4h). If the Key Vault has a private endpoint/firewall, AppGW must reach it (same/peered VNet, trusted services allowed).

### Q6. What NSG rules does an AppGW v2 subnet need?
Inbound **GatewayManager → 65200–65535** (infrastructure/health), **AzureLoadBalancer** probes, and your client traffic (80/443) from Internet or the source range. Outbound internet must not be blocked for the control plane (unless using the private-only deployment). Forgetting 65200-65535 is a classic deployment failure.

### Q7. Can you put a 0/0 UDR on the AppGW subnet to send it through FortiGate?
Historically **not supported** for v2 (breaks control-plane traffic); now possible only with the **private Application Gateway deployment** feature. Common designs instead: (a) AppGW → FortiGate → backend (UDR on AppGW subnet for **backend prefixes only**, not 0/0), or (b) FortiGate → AppGW (FortiGate does DNAT to the AppGW private IP), or (c) parallel: AppGW for web, FortiGate for everything else.

### Q8. Path-based vs multi-site routing?
**Multi-site** listener matches host header (`api.contoso.com` vs `www.contoso.com`) — up to 100+ sites on one gateway. **Path-based** rule maps `/api/*` → pool A, `/images/*` → pool B, default → pool C. Combine both.

### Q9. Health probe behaviour?
Default probe hits `/` on the backend setting's protocol/port, expects 200–399. Custom probe: path, host, interval, threshold, match status/body. Unhealthy backends → **502 Bad Gateway**. Troubleshoot with **Backend health** blade.

### Q10. Common 502 causes?
Backend NSG blocks AppGW subnet; probe path returns 401/404; backend cert CN/SAN mismatch or untrusted root (end-to-end TLS); backend timeout too low; DNS of FQDN backend not resolving (custom DNS); UDR sending return traffic somewhere else (asymmetric).

## WAF

### Q11. What does the WAF protect against?
OWASP Top 10 attacks: SQLi, XSS, LFI/RFI, command injection, protocol violations, bots (bot manager ruleset), plus **custom rules** (geo-match, IP allow/deny, rate limiting). Managed rulesets: **Microsoft DRS 2.1** (recommended) or OWASP CRS 3.x.

### Q12. Detection vs Prevention mode?
**Detection** logs matches but allows; **Prevention** blocks (403). Roll-out: start Detection, review `AzureDiagnostics`/`AGWFirewallLogs` in Log Analytics, add **exclusions** or disable specific rule IDs for false positives, then switch to Prevention.

### Q13. WAF policy scopes?
A **WAF Policy** resource can be associated **globally** (whole gateway), per **listener** (site), or per **URI path**. Most specific wins. Lets one gateway host apps with different tuning.

### Q14. Anomaly scoring?
DRS 2.x / CRS 3.x use anomaly scoring: each matched rule adds to a score (Critical 5, Error 4, Warning 3, Notice 2); request is blocked when score ≥ 5. So a single critical match blocks.

### Q15. Example KQL to find WAF blocks?
```kql
AGWFirewallLogs
| where TimeGenerated > ago(1h) and Action == "Blocked"
| summarize hits = count() by RuleId, Message, ClientIp, RequestUri
| order by hits desc
```
(Resource-specific table; legacy is `AzureDiagnostics | where Category == "ApplicationGatewayFirewallLog"`.)

### Q16. How do you scale AppGW v2?
**Autoscaling** with min/max instance count (capacity units). Set a minimum to avoid cold-start under burst; zone-redundant across 3 AZs. Size subnet for max instances (each instance uses a private IP, plus private frontend).

### Q17. AppGW for AKS?
**AGIC** (Application Gateway Ingress Controller) or the newer **Application Gateway for Containers** (separate L7 service with Gateway API support). Compare to NGINX/Envoy ingress — AppGW gives managed WAF in front of the cluster.
