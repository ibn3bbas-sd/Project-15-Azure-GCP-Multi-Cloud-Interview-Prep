output "network_self_link" {
  value = google_compute_network.vpc.self_link
}

output "subnets" {
  value = { for k, v in google_compute_subnetwork.subnet : k => v.self_link }
}

output "nat_ips" {
  value = google_compute_address.nat[*].address
}
