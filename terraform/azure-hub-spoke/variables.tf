variable "subscription_id" {
  description = "Connectivity subscription ID."
  type        = string
  default     = "00000000-0000-0000-0000-000000000000"
}

variable "location" {
  description = "Azure region."
  type        = string
  default     = "qatarcentral"
}

variable "prefix" {
  description = "Naming prefix."
  type        = string
  default     = "lz"
}

variable "hub_address_space" {
  type    = string
  default = "10.0.0.0/16"
}

variable "hub_subnets" {
  description = "Hub subnets. Bastion and Gateway subnet names are mandatory Azure names."
  type        = map(string)
  default = {
    GatewaySubnet      = "10.0.0.0/27"
    AzureBastionSubnet = "10.0.0.64/26"
    snet-fgt-external  = "10.0.1.0/24"
    snet-fgt-internal  = "10.0.2.0/24"
    snet-fgt-hasync    = "10.0.3.0/24"
    snet-appgw         = "10.0.4.0/24"
  }
}

variable "nva_ilb_ip" {
  description = "Frontend IP of the internal LB (HA ports) in front of the FortiGate pair."
  type        = string
  default     = "10.0.2.4"

  validation {
    condition     = can(cidrhost("${var.nva_ilb_ip}/32", 0))
    error_message = "nva_ilb_ip must be a valid IPv4 address."
  }
}

variable "onprem_prefixes" {
  description = "On-prem ranges that must be routed via the FortiGate."
  type        = list(string)
  default     = ["172.16.0.0/12"]
}

variable "spokes" {
  description = "Spoke VNets keyed by name."
  type = map(object({
    address_space = string
    subnets       = map(string)
  }))
  default = {
    app = {
      address_space = "10.1.0.0/16"
      subnets       = { snet-web = "10.1.1.0/24", snet-api = "10.1.2.0/24" }
    }
    data = {
      address_space = "10.2.0.0/16"
      subnets       = { snet-db = "10.2.1.0/24" }
    }
  }
}

variable "tags" {
  type = map(string)
  default = {
    env       = "demo"
    owner     = "platform-team"
    managedBy = "terraform"
  }
}
