# 04 — Azure Operations (Monitor, Log Analytics, VMs)

### Q1. Azure Monitor building blocks?
**Metrics** (time series, 93-day retention), **Logs** (Log Analytics workspace, KQL), **Activity log** (control-plane events, 90 days unless exported), **Resource logs** via **diagnostic settings**, **Alerts** (metric, log search, activity log, smart detection) → **Action groups** (email, SMS, webhook, Logic App, ITSM), **Workbooks**/Dashboards/Managed Grafana, **Application Insights**, **VM/Container Insights**.

### Q2. How do you collect VM logs today?
**Azure Monitor Agent (AMA)** + **Data Collection Rules (DCR)** that define what (perf counters, Syslog, Windows events, text logs) goes where. The legacy Log Analytics agent (MMA/OMS) is retired (Aug 2024). Deploy AMA at scale with Azure Policy (DINE) and Azure Arc for on-prem/other clouds.

### Q3. Single vs multiple Log Analytics workspaces?
Default to **one central workspace per region/environment** (simpler querying, Sentinel, cost commitment tiers). Split for data sovereignty, very different retention, or strict access separation — but prefer **resource-context RBAC** / table-level RBAC over many workspaces.

### Q4. How do you control Log Analytics cost?
Commitment tiers; **Basic/Auxiliary logs** tables for high-volume low-value data; DCR **transformations** to drop/filter columns at ingestion; per-table retention and archive; daily cap (careful — causes data loss); avoid duplicate diagnostic settings.

### Q5. Five KQL queries you should know
```kql
// 1) Heartbeat — which VMs stopped reporting
Heartbeat | summarize last = max(TimeGenerated) by Computer
| where last < ago(10m)

// 2) Top CPU
Perf | where ObjectName == "Processor" and CounterName == "% Processor Time"
| summarize avg(CounterValue) by Computer, bin(TimeGenerated, 5m) | top 10 by avg_CounterValue

// 3) Who deleted a resource
AzureActivity | where OperationNameValue endswith "DELETE" and ActivityStatusValue == "Success"
| project TimeGenerated, Caller, ResourceGroup, _ResourceId

// 4) Failed sign-ins (Entra logs routed to workspace)
SigninLogs | where ResultType != "0" | summarize count() by UserPrincipalName, IPAddress

// 5) Syslog errors
Syslog | where SeverityLevel in ("err","crit","alert","emerg") | summarize count() by Computer, ProcessName
```

### Q6. Metric alert vs log search alert?
**Metric alerts**: near real-time (1 min), cheap, stateful, dimension splitting — CPU, LB health probe status, AppGW unhealthy host count. **Log search alerts**: any KQL, 1–15+ min frequency, good for correlation/absence. Use **dynamic thresholds** for noisy metrics.

### Q7. What would you monitor for the hub?
FortiGate: ILB **health probe status** (DipAvailability), VM CPU/sessions, FortiGate syslog to workspace/FortiAnalyzer. VPN gateway: tunnel ingress/egress, **TunnelBandwidth**, BGP peer status. AppGW: unhealthy host count, failed requests, WAF blocks, capacity units. Bastion: sessions. Plus **Connection Monitor** for on-prem ↔ spoke latency/loss.

### Q8. VM availability options?
**Availability set** (fault/update domains in a datacenter, 99.95%), **Availability zones** (separate datacenters, 99.99% for 2+ VMs across zones), **VMSS** (autoscale, Flexible orchestration recommended). Single VM with Premium SSD: 99.9%.

### Q9. How do you patch VMs at scale?
**Azure Update Manager** — periodic assessment, maintenance configurations (schedules), works for Arc servers too. Hotpatch for Windows Server Azure Edition. Pair with Defender for Servers vulnerability assessment.

### Q10. VM disk encryption options?
Server-side encryption (SSE) with platform keys by default; **CMK** via Disk Encryption Set + Key Vault; **encryption at host** (encrypts temp disk & caches); Azure Disk Encryption (BitLocker/dm-crypt in-guest — being phased toward encryption at host); Confidential VMs for in-use protection.

### Q11. How do you back up and DR VMs?
**Azure Backup** (Recovery Services vault, policies, soft delete, immutability, cross-region restore). **Azure Site Recovery** for DR replication to another region with recovery plans and test failover — note Saudi region pairing/availability when designing.

### Q12. Serial console / boot diagnostics — why do you care?
When a VM is unreachable (bad NSG, firewall, sshd broken, fstab), **boot diagnostics** screenshot + **serial console** gives out-of-band access. Similar to my OCI console-connection recovery work.
