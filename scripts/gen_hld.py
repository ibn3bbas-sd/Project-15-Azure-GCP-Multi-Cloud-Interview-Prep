#!/usr/bin/env python3
"""Generate docs/hld-azure-gcp-multicloud.svg (1920x1080, light + dark theme).

Usage: python scripts/gen_hld.py [output.svg]
"""
import sys
from xml.sax.saxutils import escape

FONT = "'Inter','Segoe UI','Noto Sans','DejaVu Sans',Helvetica,Arial,sans-serif"
from pathlib import Path

HERE = Path(__file__).resolve().parent
GCP_SYMBOLS = (HERE / "assets" / "gcp-symbols.xml").read_text(encoding="utf-8")
OUT = sys.argv[1] if len(sys.argv) > 1 else str(HERE.parent / "docs" / "hld-azure-gcp-multicloud.svg")

LIGHT = dict(bg="#ffffff", dots="url(#dots-lt)", text="#1f2328", sub="#57606a", muted="#8c959f",
             panel="#f6f8fa", border="#d0d7de", tile="#ffffff", fillbox="#0b1220",
             blue="#2e90fa", azure="#0078d4", gblue="#0969da", orange="#f79009", dorange="#e8590c",
             red="#e8422e", green="#12b76a", teal="#0e9384", purple="#9e77ed", indigo="#6172f3",
             slate="#64748b")
DARK = dict(bg="#0d1117", dots="url(#dots-dk)", text="#e6edf3", sub="#8b949e", muted="#7d8590",
            panel="#161b22", border="#30363d", tile="#ffffff", fillbox="#ffffff",
            blue="#58a6ff", azure="#4aa3ff", gblue="#58a6ff", orange="#ffab4d", dorange="#ff9a4d",
            red="#ff7b6b", green="#3fd68b", teal="#2dd4bf", purple="#b692f6", indigo="#8f9bff",
            slate="#8b949e")

def circ(cx, cy, r):
    return f"M{cx-r} {cy}a{r} {r} 0 1 0 {2*r} 0a{r} {r} 0 1 0 {-2*r} 0"

GLYPH = {
    "users": "M8 11a3.2 3.2 0 1 0 0-6.4A3.2 3.2 0 0 0 8 11z M2.5 19.5c0-3 2.5-5 5.5-5s5.5 2 5.5 5 M16 11.5a2.6 2.6 0 1 0 0-5.2 M15.5 14.8c2.8.2 5 2.1 5 4.7",
    "building": "M4 20V6l8-3 8 3v14 M2.5 20h19 M10 20v-4h4v4 M8 9h.01 M12 9h.01 M16 9h.01 M8 12.5h.01 M12 12.5h.01 M16 12.5h.01",
    "pipeline": "M3.5 5h6v5h-6z M14.5 14h6v5h-6z M9.5 7.5h3.5a2 2 0 0 1 2 2V14 M6.5 10v4.5a2 2 0 0 0 2 2h6",
    "git": f"{circ(6,5,2)} {circ(6,19,2)} {circ(18,7,2)} M6 7v10 M18 9c0 4.5-6 3.5-11.2 8.4",
    "shield": "M12 3.2l7 2.8v5.2c0 4.2-2.9 7.6-7 9.6-4.1-2-7-5.4-7-9.6V6z M9 12l2.2 2.2L15.4 10",
    "firewall": "M3 5h18v14H3z M3 9.7h18 M3 14.3h18 M9 5v4.7 M15 5v4.7 M6 9.7v4.6 M12 9.7v4.6 M18 9.7v4.6 M9 14.3V19 M15 14.3V19",
    "vpn": "M7 11V8a5 5 0 0 1 10 0v3 M5 11h14v9H5z M12 14.5v2.5",
    "globe": "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18z M3 12h18 M12 3c2.5 2.5 3.8 5.5 3.8 9s-1.3 6.5-3.8 9 M12 3c-2.5 2.5-3.8 5.5-3.8 9s1.3 6.5 3.8 9",
    "terminal": "M3.5 5h17v14h-17z M7.5 10l3 2.5-3 2.5 M12.5 15h4",
    "key": f"{circ(8,12,4)} M12 12h9 M18 12v3 M21 12v2",
    "id": f"M3.5 5h17v14h-17z {circ(9,10.5,2)} M5.8 16.2c.6-1.7 1.8-2.5 3.2-2.5s2.6.8 3.2 2.5 M14.5 9.5h3.5 M14.5 13h3.5",
    "chart": "M4 20h16 M7 17v-5 M11 17V7 M15 17v-8 M19 17v-3",
    "network": "M9.5 3h5v4h-5z M3 16h5v4H3z M9.5 16h5v4h-5z M16 16h5v4h-5z M12 7v5 M5.5 16v-4h13v4 M12 12v4",
    "policy": "M6 3h9l4 4v14H6z M15 3v4h4 M9 13.5l2 2 4-4",
    "lb": "M12 3.5v5 M4 20v-4.5h16V20 M12 8.5v7 M8.5 3h7 M2.5 20h3 M10.5 20h3 M18.5 20h3",
    "folder": "M3 6h7l2 2h9v11H3z",
    "router": "M4 12h16 M16 8l4 4-4 4 M8 8l-4 4 4 4",
    "nat": "M4 7h13 M14 4l3 3-3 3 M20 17H7 M10 14l-3 3 3 3",
    "perimeter": "M4 4h16v16H4z M8 8h8v8H8z",
    "db": "M5 6c0-1.7 3.1-3 7-3s7 1.3 7 3-3.1 3-7 3-7-1.3-7-3z M5 6v12c0 1.7 3.1 3 7 3s7-1.3 7-3V6 M5 12c0 1.7 3.1 3 7 3s7-1.3 7-3",
    "radar": f"{circ(12,12,8.5)} {circ(12,12,4.5)} M12 12l6-6",
    "doc": "M6 3h9l4 4v14H6z M15 3v4h4 M9 12h6 M9 15.5h6",
}


class SVG:
    def __init__(self, p):
        self.p, self.o = p, []

    def c(self, k):
        return self.p.get(k, k)

    def add(self, s):
        self.o.append(s)

    def text(self, x, y, t, size=12, weight=400, fill="text", anchor="start", ls=0):
        self.add(f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" '
                 f'fill="{self.c(fill)}" text-anchor="{anchor}" letter-spacing="{ls}">{escape(t)}</text>')

    def rect(self, x, y, w, h, rx=10, fill="panel", stroke="border", sw=1.4, dash=None, fo=None, so=None):
        a = f' stroke-dasharray="{dash}"' if dash else ""
        a += f' fill-opacity="{fo}"' if fo is not None else ""
        a += f' stroke-opacity="{so}"' if so is not None else ""
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" ry="{rx}" fill="{self.c(fill)}" '
                 f'stroke="{self.c(stroke)}" stroke-width="{sw}"{a}/>')

    def glyph(self, x, y, size, kind, color):
        self.rect(x, y, size, size, rx=round(size * 0.26, 2), fill=color, stroke=color, sw=0)
        pad = size * 0.09
        sc = (size - 2 * pad) / 24
        self.add(f'<g transform="translate({x+pad:.1f},{y+pad:.1f}) scale({sc:.3f})" fill="none" stroke="#fff" '
                 f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="{GLYPH[kind]}"/></g>')

    def gicon(self, x, y, size, sym):
        self.rect(x, y, size, size, rx=round(size * 0.22, 2), fill="tile", stroke="border", sw=1)
        i = size * 0.72
        self.add(f'<use href="#gcp-{sym}" x="{x+(size-i)/2:.1f}" y="{y+(size-i)/2:.1f}" width="{i:.1f}" height="{i:.1f}"/>')

    def arrow(self, pts, color, dash=None, w=1.8, head=True, both=False):
        d = "M" + " L".join(f"{x} {y}" for x, y in pts)
        a = f' stroke-dasharray="{dash}"' if dash else ""
        col = self.c(color)
        self.add(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{w}" stroke-linecap="round" '
                 f'stroke-linejoin="round" opacity="0.95"{a}/>')
        if head:
            self._head(pts[-2], pts[-1], col)
        if both:
            self._head(pts[1], pts[0], col)

    def _head(self, a, b, col):
        (x1, y1), (x2, y2) = a, b
        if x1 == x2:
            s = 1 if y2 > y1 else -1
            p = f"{x2},{y2} {x2-2.9},{y2-6.4*s} {x2+2.9},{y2-6.4*s}"
        else:
            s = 1 if x2 > x1 else -1
            p = f"{x2},{y2} {x2-6.4*s},{y2-2.9} {x2-6.4*s},{y2+2.9}"
        self.add(f'<polygon points="{p}" fill="{col}" opacity="0.95"/>')

    # ---- composite pieces ----
    def boundary(self, x, y, w, h, color, label, icon=None, gsym=None, dash="10 7", tabw=None):
        self.rect(x, y, w, h, rx=14, fill="fillbox", stroke=color, sw=2.2, dash=dash, fo=0.028, so=0.95)
        tw = tabw or (len(label) * 8.1 + 52)
        self.rect(x + 16, y - 18, tw, 36, rx=9, fill="bg", stroke=color, sw=1.6)
        if gsym:
            self.gicon(x + 22, y - 13, 26, gsym)
        else:
            self.glyph(x + 22, y - 13, 26, icon, color)
        self.text(x + 56, y + 5.5, label, 14.5, 600, color)

    def card(self, x, y, w, h, color, icon, kicker, title, lines, gsym=None, dash="5 4"):
        self.rect(x, y, w, h, rx=10, fill="fillbox", stroke=color, sw=1.5, dash=dash, fo=0.04, so=0.9)
        if gsym:
            self.gicon(x + 12, y + 12, 28, gsym)
        else:
            self.glyph(x + 12, y + 12, 28, icon, color)
        self.text(x + 48, y + 26, kicker, 10.2, 600, "muted", ls=0.6)
        self.text(x + 48, y + 41, title, 13.5, 700, color)
        for i, ln in enumerate(lines):
            self.text(x + 14, y + 64 + i * 15, ln, 11.3, 400, "text" if i == 0 else "sub")

    def actor(self, cx, icon, color, title, sub):
        self.glyph(cx - 24, 146, 48, icon, color)
        self.text(cx, 214, title, 13.5, 650, "text", "middle")
        self.text(cx, 230, sub, 11.4, 400, "sub", "middle")

    def bullets(self, x, y, items, color="gblue"):
        for i, (a, b) in enumerate(items):
            yy = y + i * 31
            self.add(f'<circle cx="{x+2}" cy="{yy-4}" r="2.8" fill="{self.c(color)}"/>')
            self.text(x + 14, yy, a, 11.8, 400, "text")
            self.text(x + 14, yy + 14, b, 11.8, 400, "sub")

    def label(self, x, y, t, color, anchor="middle", pill=False):
        if pill and t:
            w = len(t) * 6.3 + 16
            x0 = x - w / 2 if anchor == "middle" else x - 8
            self.rect(round(x0, 1), y - 14, round(w, 1), 20, rx=6, fill="bg", stroke="border", sw=1)
        self.text(x, y, t, 11.5, 600, color, anchor)


def flows(s):
    # Internet -> AppGW (ingress)
    s.arrow([(600, 240), (600, 414)], "blue")
    s.label(560, 312, "HTTPS 443", "blue")
    # On-prem -> Azure VPN GW
    s.arrow([(760, 240), (760, 414)], "purple", dash="7 5", both=True)
    # On-prem -> GCP HA VPN
    s.arrow([(776, 240), (776, 304), (1060, 304), (1060, 414)], "purple", dash="7 5")
    s.label(830, 320, "IPsec · BGP", "purple")
    # Azure VPN GW <-> GCP HA VPN
    s.arrow([(894, 468), (992, 468)], "purple", dash="7 5", both=True)
    # AppGW -> FortiGate (inspect)
    s.arrow([(628, 500), (634, 500), (634, 586), (640, 586)], "orange", dash="7 5")
    # Spokes -> FortiGate via UDR
    s.arrow([(485, 684), (485, 664), (700, 664), (700, 640)], "orange", dash="7 5")
    s.arrow([(775, 684), (775, 640)], "orange", dash="7 5")
    s.label(560, 678, "UDR 0/0 → ILB", "orange")
    # Engineers -> ADO
    s.arrow([(1030, 170), (1170, 170)], "slate")
    s.text(1100, 162, "PR merge", 10.5, 600, "slate", "middle")
    # ADO -> Azure / GCP (deploy, OIDC)
    s.arrow([(1188, 240), (1188, 318), (900, 318), (900, 342)], "teal")
    s.arrow([(1212, 240), (1212, 342)], "teal")
    s.label(1250, 330, "OIDC · WIF", "teal")
    # Entra ID SSO -> GCP (workforce) dotted
    s.arrow([(1380, 240), (1380, 342)], "indigo", dash="3 4")
    s.label(1372, 316, "SSO", "indigo", "end")
    # Cloud NAT egress
    s.arrow([(1408, 452), (1452, 452), (1452, 300)], "red", w=1.8)
    s.text(1446, 318, "internet", 11, 600, "red", "end")
    s.text(1446, 332, "egress", 11, 600, "red", "end")



def draw(s: SVG):
    s.add(f'<rect width="1920" height="1080" fill="{s.c("bg")}"/>')
    s.add(f'<rect width="1920" height="1080" fill="{s.c("dots")}"/>')

    # ---------------- header ----------------
    s.text(48, 52, "Azure & GCP Multi-Cloud Landing Zone — High-Level Design (HLD)", 30, 700)
    s.text(48, 78, "Azure hub-and-spoke with FortiGate NVA · GCP Shared VPC with VPC Service Controls · "
                   "hybrid IPsec + BGP · Terraform delivered by Azure DevOps Plan → Approval → Apply", 15.5, 400, "sub")
    s.text(1880, 52, "FHD 1920 × 1080", 14, 600, "muted", "end")
    s.text(1880, 74, "Project-15 · reference design v1.0 · interview whiteboard", 13.5, 400, "muted", "end")
    flows(s)
    s.add(f'<line x1="48" y1="96" x2="1880" y2="96" stroke="{s.c("border")}" stroke-width="1.5" opacity="0.9"/>')

    # ---------------- left sidebar ----------------
    s.rect(48, 120, 250, 352, rx=12)
    s.text(66, 152, "At a glance", 16.5, 700)
    s.bullets(68, 176, [
        ("Hub-and-spoke on Azure, ALZ", "management-group hierarchy"),
        ("FortiGate A/P behind ILB HA", "ports inspects N-S and E-W"),
        ("Spokes: UDR 0/0 → 10.0.2.4,", "gateway route propagation off"),
        ("App Gateway WAF v2 is the", "only internet ingress"),
        ("GCP Shared VPC per env, host", "owns subnets, NAT, VPN"),
        ("VPC-SC perimeter blocks data", "exfiltration from APIs"),
        ("Pipelines use OIDC / WIF —", "no stored secrets or SA keys"),
        ("No public IPs on workloads —", "Bastion and IAP only"),
        ("Azure ↔ GCP ↔ on-prem over", "IPsec with BGP failover"),
    ])

    s.rect(48, 490, 250, 262, rx=12)
    s.text(66, 522, "IaC delivery", 16.5, 700)
    s.text(66, 542, "Terraform · Azure DevOps YAML", 12, 400, "sub")
    steps = [("PR", "fmt · tflint · Checkov", "blue"),
             ("Plan", "plan -out → artifact", "indigo"),
             ("Approve", "approvals + exclusive lock", "orange"),
             ("Apply", "apply saved plan only", "green"),
             ("Drift", "nightly plan · exit 2", "purple")]
    for i, (a, b, col) in enumerate(steps):
        y = 556 + i * 36
        s.rect(66, y, 214, 28, rx=7, fill="bg", stroke=col, sw=1.3)
        s.text(76, y + 18.5, a, 11.8, 700, col)
        s.text(130, y + 18.5, b, 10.6, 400, "sub")
        if i < len(steps) - 1:
            s.arrow([(86, y + 28), (86, y + 36)], col, w=1.4)
    s.text(66, 744, "State: azurerm blob lease · GCS lock", 10.8, 400, "sub")

    s.rect(48, 770, 250, 250, rx=12)
    s.text(66, 802, "Guardrails", 16.5, 700)
    s.text(66, 826, "Azure Policy (Corp LZ)", 12, 700, "azure")
    for i, t in enumerate(["Deny public IP on NICs", "Deny subnet without NSG",
                           "Allowed locations · required tags", "DINE: diagnostics + Defender"]):
        s.text(66, 845 + i * 16, t, 11.2, 400, "sub")
    s.text(66, 918, "GCP Org Policy (folder)", 12, 700, "gblue")
    for i, t in enumerate(["compute.vmExternalIpAccess = deny", "iam.disableServiceAccountKeyCreation",
                           "gcp.resourceLocations = me-central2", "skipDefaultNetworkCreation"]):
        s.text(66, 937 + i * 16, t, 11.2, 400, "sub")

    # ---------------- actors ----------------
    s.rect(336, 140, 210, 110, rx=11)
    s.text(352, 164, "Inspect everything", 13, 700)
    for i, t in enumerate(["N-S and E-W traffic passes", "the FortiGate; Google APIs stay",
                           "inside the VPC-SC perimeter;", "only NAT IPs leave GCP."]):
        s.text(352, 184 + i * 15, t, 11.2, 400, "sub")

    s.actor(600, "globe", "blue", "Internet users", "HTTPS 443")
    s.actor(767, "building", "purple", "On-prem DC", "FortiGate · IPsec · BGP")
    s.actor(1000, "git", "slate", "Platform engineers", "Git · PR · CODEOWNERS")
    s.actor(1200, "pipeline", "teal", "Azure DevOps", "YAML pipelines · OIDC")
    s.actor(1380, "id", "indigo", "Entra ID", "SSO · MFA · PIM")

    s.rect(660, 262, 780, 28, rx=8)
    s.text(1050, 281, "Hybrid & cross-cloud transit · IPsec IKEv2 + BGP · on-prem FortiGate ↔ Azure VPN GW (A/A) ↔ GCP HA VPN",
           11.6, 600, "sub", "middle")

    # ---------------- Azure boundary ----------------
    s.boundary(330, 340, 600, 680, "azure", "Microsoft Azure · ALZ", icon="network", tabw=232)

    # Hub VNet
    s.rect(350, 384, 560, 268, rx=14, fill="fillbox", stroke="dorange", sw=2.2, dash="8 6", fo=0.028, so=0.95)
    s.rect(366, 366, 392, 36, rx=9, fill="bg", stroke="dorange", sw=1.6)
    s.glyph(372, 371, 26, "network", "dorange")
    s.text(406, 389.5, "Hub VNet · 10.0.0.0/16 · connectivity sub", 14.5, 600, "dorange")

    s.card(366, 414, 262, 108, "blue", "lb", "AppGW subnet", "App Gateway WAF v2",
           ["DRS 2.1 · Prevention · TLS 1.2+", "cert from Key Vault via UAMI", "GatewayManager 65200–65535"])
    s.card(640, 414, 254, 108, "purple", "vpn", "GatewaySubnet", "VPN Gateway (A/A)",
           ["IPsec IKEv2 · BGP ASN 65515", "UDR: spokes → FortiGate ILB", "gateway transit to spokes"])
    s.card(366, 532, 262, 108, "slate", "terminal", "AzureBastionSubnet /26", "Azure Bastion",
           ["RDP/SSH over 443 · no VM PIPs", "native client tunneling", "reaches peered spokes"])
    s.card(640, 532, 254, 108, "red", "firewall", "fgt-ext · fgt-int · ha-sync", "FortiGate A/P (FGCP)",
           ["ILB HA ports → 10.0.2.4", "ELB inbound · SNAT for symmetry", "IP forwarding on NICs"])

    # Spokes
    s.card(350, 684, 270, 116, "green", "network", "spoke · LZ subscription", "Spoke-app 10.1.0.0/16",
           ["snet-web · snet-api (VMs / AKS)", "UDR 0/0 → 10.0.2.4", "NSG: 22/3389 from Bastion only"])
    s.card(640, 684, 270, 116, "teal", "db", "spoke · LZ subscription", "Spoke-data 10.2.0.0/16",
           ["snet-db · private endpoints", "BGP propagation off", "NSG: app tier → db ports only"])
    s.text(350, 822, "Peering: hub allow gateway transit · spokes use remote gateways · allow forwarded traffic · non-transitive",
           10.6, 400, "sub")

    # Azure platform services
    for x in (418, 560, 702, 844):
        s.arrow([(x, 834), (x, 868)], "azure", w=1.6)
    s.label(630, 852, "Private endpoints · diagnostic settings", "azure", pill=True)
    svc = [("indigo", "id", "identity", "Entra ID", ["JIT roles · CA policies", "managed identities", "WIF fed. credentials"]),
           ("orange", "key", "secrets", "Key Vault", ["RBAC model", "purge protection", "private endpoint"]),
           ("green", "shield", "posture", "Defender", ["CSPM · secure score", "Servers · Containers", "→ Sentinel"]),
           ("blue", "chart", "operations", "Monitor", ["AMA + DCR · KQL", "VNet flow logs", "alerts → action grp"])]
    for i, (col, ic, k, t, ls) in enumerate(svc):
        s.card(350 + i * 142, 872, 134, 132, col, ic, k, t, ls, dash=None)

    # ---------------- GCP boundary ----------------
    s.boundary(960, 340, 480, 680, "gblue", "Google Cloud · Org", gsym="virtual_private_cloud", tabw=200)

    s.rect(976, 384, 448, 196, rx=14, fill="fillbox", stroke="dorange", sw=2.2, dash="8 6", fo=0.028, so=0.95)
    s.rect(992, 366, 392, 36, rx=9, fill="bg", stroke="dorange", sw=1.6)
    s.gicon(998, 371, 26, "virtual_private_cloud")
    s.text(1032, 389.5, "Host project · Shared VPC prod-vpc (global)", 14.5, 600, "dorange")
    s.card(992, 414, 204, 108, "purple", "router", "Cloud Router", "HA VPN + BGP",
           ["99.99% · 2 tunnels", "ASN 64514 · global routing", "adv. 199.36.153.4/30"])
    s.card(1208, 414, 200, 108, "red", None, "egress", "Cloud NAT",
           ["2 static IPs (allow-list)", "dynamic port allocation", "logs: ERRORS_ONLY"], gsym="cloud_nat")
    s.text(992, 546, "Subnets (me-central2): app 10.10.0.0/20 + pods/services ranges", 11, 400, "text")
    s.text(992, 562, "data 10.10.16.0/20 · Private Google Access · flow logs · IAP 35.235.240.0/20", 11, 400, "sub")

    # VPC-SC perimeter
    for x in (1094, 1308):
        s.arrow([(x, 646), (x, 580)], "green", w=1.6)
    s.rect(976, 616, 448, 200, rx=14, fill="fillbox", stroke="red", sw=2.2, dash="8 6", fo=0.028, so=0.95)
    s.rect(992, 598, 340, 36, rx=9, fill="bg", stroke="red", sw=1.6)
    s.glyph(998, 603, 26, "perimeter", "red")
    s.text(1032, 621.5, "VPC-SC perimeter · dry-run → enforce", 14.5, 600, "red")
    s.card(992, 646, 204, 116, "green", None, "service project", "app-prod",
           ["GKE / VMs on app subnet", "networkUser on subnet", "Workload Identity (KSA)"], gsym="google_kubernetes_engine")
    s.card(1208, 646, 200, 116, "teal", None, "service project", "data-prod",
           ["BigQuery · GCS (CMEK)", "restricted.googleapis.com", "ingress: deploy SA only"], gsym="cloud_storage")
    s.text(992, 786, "Access levels + ingress/egress rules · Cloud Build private pool", 10.8, 400, "sub")
    s.text(992, 802, "Shared VPC admin: compute.xpnAdmin at folder", 10.8, 400, "sub")

    # GCP platform services
    for x in (1048, 1200, 1352):
        s.arrow([(x, 834), (x, 868)], "teal", w=1.6)
    s.label(1200, 852, "Private Google Access · org log sink", "teal", pill=True)
    gsvc = [("orange", "key", None, "keys", "Cloud KMS", ["CMEK · HSM level", "90-day rotation", "separate sec project"]),
            ("green", "radar", None, "posture", "SCC", ["SHA · ETD findings", "→ Pub/Sub → SIEM", "CIS / PCI reports"]),
            ("blue", None, "cloud_logging", "audit", "Logging", ["aggregated org sink", "_Required 400 days", "→ Sentinel"])]
    for i, (col, ic, gs, k, t, ls) in enumerate(gsvc):
        s.card(976 + i * 152, 872, 144, 132, col, ic, k, t, ls, gsym=gs, dash=None)

    s.rect(913, 476, 64, 20, rx=6, fill="bg", stroke="purple", sw=1)
    s.text(945, 490, "4 tunnels", 10.5, 600, "purple", "middle")

    # ---------------- right panel ----------------
    s.rect(1466, 120, 414, 902, rx=12)
    s.text(1484, 152, "Abbreviations", 16.5, 700)
    s.text(1484, 172, "every acronym used in this diagram", 12, 400, "sub")
    groups = [
        ("AZURE", "azure", [("ALZ", "Azure Landing Zone"), ("VNet", "Virtual Network"), ("UDR", "User-Defined Route"),
                            ("NVA", "Network Virtual Appliance"), ("ILB", "Internal Load Balancer"),
                            ("FGCP", "FortiGate Clustering Protocol"), ("WAF", "Web Application Firewall"),
                            ("UAMI", "User-Assigned Managed Identity"), ("PIM", "Privileged Identity Management")]),
        ("GOOGLE CLOUD", "gblue", [("VPC-SC", "VPC Service Controls"), ("NAT", "Network Address Translation"),
                                   ("IAP", "Identity-Aware Proxy"), ("WIF", "Workload Identity Federation"),
                                   ("KMS", "Key Management Service"), ("CMEK", "Customer-Managed Encryption Key"),
                                   ("SCC", "Security Command Center")]),
        ("PLATFORM", "green", [("IaC", "Infrastructure as Code"), ("OIDC", "OpenID Connect"),
                               ("BGP", "Border Gateway Protocol"), ("ASN", "Autonomous System Number"),
                               ("A/A · A/P", "Active-Active · Active-Passive"), ("DRS", "Default Rule Set (WAF)"),
                               ("CSPM", "Cloud Security Posture Mgmt")]),
    ]
    y = 202
    for name, col, items in groups:
        s.text(1490, y, name, 11.5, 700, "muted", ls=0.8)
        s.add(f'<line x1="1490" y1="{y+8}" x2="1856" y2="{y+8}" stroke="{s.c("border")}" stroke-width="1"/>')
        y += 26
        for a, b in items:
            s.rect(1490, y - 10, 3, 12, rx=1.5, fill=col, stroke=col, sw=0)
            s.text(1504, y, a, 13.2, 650)
            s.text(1590, y, b, 12.4, 400, "sub")
            y += 21
        y += 12
    s.text(1490, y + 4, "FLOW KEY", 11.5, 700, "muted", ls=0.8)
    y += 26
    keys = [("blue", None, "Ingress — internet users via App Gateway WAF"),
            ("purple", "7 5", "Hybrid — IPsec + BGP (on-prem, Azure, GCP)"),
            ("orange", "7 5", "Inspection — UDR to FortiGate ILB"),
            ("teal", None, "Delivery — Azure DevOps via OIDC / WIF"),
            ("green", None, "Shared VPC — service projects use host subnets"),
            ("indigo", "3 4", "Identity — Entra ID SSO / federation"),
            ("red", None, "Egress — Cloud NAT static IPs")]
    for col, dash, t in keys:
        s.arrow([(1504, y), (1552, y)], col, dash=dash, w=2.2)
        s.text(1580, y + 4, t, 12.4, 400, "sub")
        y += 22

    # ---------------- footer ----------------
    s.add(f'<line x1="48" y1="1032" x2="1880" y2="1032" stroke="{s.c("border")}" stroke-width="1.2" opacity="0.8"/>')
    s.text(48, 1053, "Ingress: Internet → App Gateway WAF → FortiGate → spoke   ·   East-west: spoke → UDR → FortiGate ILB → spoke   ·   "
                     "Hybrid: on-prem FortiGate ⇄ Azure VPN GW / GCP HA VPN (BGP)   ·   Deploy: PR → ADO plan → approval → apply", 13, 400, "sub")
    s.text(48, 1072, "Reference design for interview discussion · IP ranges and ASNs are examples · no customer data", 12, 400, "muted")


def build():
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080" role="img" '
             'aria-label="Azure and GCP multi-cloud landing zone high-level design">',
             '<style>.theme-dark{display:none}@media (prefers-color-scheme: dark){.theme-light{display:none}.theme-dark{display:inline}}</style>',
             '<defs><pattern id="dots-lt" width="32" height="32" patternUnits="userSpaceOnUse"><circle cx="1.2" cy="1.2" r="1.2" fill="#eef1f4"/></pattern>'
             '<pattern id="dots-dk" width="32" height="32" patternUnits="userSpaceOnUse"><circle cx="1.2" cy="1.2" r="1.2" fill="#161b22"/></pattern>',
             GCP_SYMBOLS, '</defs>']
    for cls, pal in (("theme-light", LIGHT), ("theme-dark", DARK)):
        s = SVG(pal)
        draw(s)
        parts.append(f'<g class="{cls}">')
        parts.extend(s.o)
        parts.append('</g>')
    parts.append('</svg>')
    open(OUT, "w", encoding="utf-8").write("\n".join(parts))


if __name__ == "__main__":
    build()
