# -----------------------------------------------------------------------------
# GCP Shared VPC: host project, custom-mode VPC, subnets with PGA, Cloud Router,
# Cloud NAT, baseline firewall, subnet-level IAM, and org-policy guardrails.
# Interview talking points are marked with  >>>
# -----------------------------------------------------------------------------

# >>> Host project owns the network; service projects only consume subnets.
resource "google_compute_shared_vpc_host_project" "host" {
  project = var.host_project_id
}

resource "google_compute_shared_vpc_service_project" "svc" {
  for_each        = var.service_projects
  host_project    = google_compute_shared_vpc_host_project.host.project
  service_project = each.key
}

# >>> Custom mode only — auto mode creates overlapping /20s in every region.
resource "google_compute_network" "vpc" {
  project                         = var.host_project_id
  name                            = "prod-vpc"
  auto_create_subnetworks         = false
  routing_mode                    = "GLOBAL" # Cloud Router learned routes reach all regions
  delete_default_routes_on_create = false
}

resource "google_compute_subnetwork" "subnet" {
  for_each                 = var.subnets
  project                  = var.host_project_id
  name                     = "${each.key}-${var.region}"
  region                   = var.region
  network                  = google_compute_network.vpc.id
  ip_cidr_range            = each.value.cidr
  private_ip_google_access = true # >>> reach Google APIs without external IPs

  dynamic "secondary_ip_range" {
    for_each = each.value.secondary
    content {
      range_name    = secondary_ip_range.key
      ip_cidr_range = secondary_ip_range.value
    }
  }

  log_config {
    aggregation_interval = "INTERVAL_5_SEC"
    flow_sampling        = 0.5
    metadata             = "INCLUDE_ALL_METADATA"
  }
}

# >>> Least privilege: networkUser on the SUBNET, not the whole host project.
resource "google_compute_subnetwork_iam_member" "network_user" {
  for_each   = var.service_projects
  project    = var.host_project_id
  region     = var.region
  subnetwork = google_compute_subnetwork.subnet[each.value.subnet].name
  role       = "roles/compute.networkUser"
  member     = each.value.principal
}

# >>> Cloud Router = BGP control plane (HA VPN / Interconnect) and NAT host.
resource "google_compute_router" "router" {
  project = var.host_project_id
  name    = "cr-${var.region}"
  region  = var.region
  network = google_compute_network.vpc.id

  bgp {
    asn               = 64514
    advertise_mode    = "CUSTOM"
    advertised_groups = ["ALL_SUBNETS"]

    # Advertise restricted Google APIs VIP to on-prem (VPC-SC friendly).
    advertised_ip_ranges {
      range       = "199.36.153.4/30"
      description = "restricted.googleapis.com"
    }
  }
}

# >>> Static NAT IPs so partners can allow-list our egress.
resource "google_compute_address" "nat" {
  count   = 2
  project = var.host_project_id
  name    = "nat-${var.region}-${count.index}"
  region  = var.region
}

resource "google_compute_router_nat" "nat" {
  project                             = var.host_project_id
  name                                = "nat-${var.region}"
  router                              = google_compute_router.router.name
  region                              = var.region
  nat_ip_allocate_option              = "MANUAL_ONLY"
  nat_ips                             = google_compute_address.nat[*].self_link
  source_subnetwork_ip_ranges_to_nat  = "ALL_SUBNETWORKS_ALL_IP_RANGES"
  enable_dynamic_port_allocation      = true
  min_ports_per_vm                    = 64
  max_ports_per_vm                    = 4096
  enable_endpoint_independent_mapping = false # must be false with dynamic port allocation

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

# ---------------- Baseline firewall ----------------
resource "google_compute_firewall" "deny_all_ingress" {
  project   = var.host_project_id
  name      = "deny-all-ingress"
  network   = google_compute_network.vpc.id
  direction = "INGRESS"
  priority  = 65000

  deny {
    protocol = "all"
  }

  source_ranges = ["0.0.0.0/0"]

  log_config {
    metadata = "INCLUDE_ALL_METADATA"
  }
}

# >>> IAP TCP forwarding range — the "Bastion" equivalent for SSH/RDP.
resource "google_compute_firewall" "allow_iap" {
  project   = var.host_project_id
  name      = "allow-iap-ssh-rdp"
  network   = google_compute_network.vpc.id
  direction = "INGRESS"
  priority  = 1000

  allow {
    protocol = "tcp"
    ports    = ["22", "3389"]
  }

  source_ranges = ["35.235.240.0/20"]
}

resource "google_compute_firewall" "allow_health_checks" {
  project   = var.host_project_id
  name      = "allow-gfe-health-checks"
  network   = google_compute_network.vpc.id
  direction = "INGRESS"
  priority  = 1000

  allow {
    protocol = "tcp"
  }

  source_ranges = ["35.191.0.0/16", "130.211.0.0/22"]
}

# ---------------- Org policy guardrails (folder level) ----------------
# >>> Like Azure Policy "deny": applies regardless of who has IAM.
resource "google_org_policy_policy" "no_external_ip" {
  name   = "${var.folder_id}/policies/compute.vmExternalIpAccess"
  parent = var.folder_id

  spec {
    rules {
      deny_all = "TRUE"
    }
  }
}

resource "google_org_policy_policy" "no_sa_keys" {
  name   = "${var.folder_id}/policies/iam.disableServiceAccountKeyCreation"
  parent = var.folder_id

  spec {
    rules {
      enforce = "TRUE"
    }
  }
}

resource "google_org_policy_policy" "resource_locations" {
  name   = "${var.folder_id}/policies/gcp.resourceLocations"
  parent = var.folder_id

  spec {
    rules {
      values {
        allowed_values = ["in:me-central2-locations"]
      }
    }
  }
}
