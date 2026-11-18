# -----------------------------------------------------------------------------
# Hub-and-spoke with FortiGate NVA (FortiGate VMs + LBs omitted for brevity:
# deploy them from Fortinet's Azure Terraform templates and pass the ILB IP).
# Interview talking points are marked with  >>>
# -----------------------------------------------------------------------------

locals {
  spoke_prefixes = { for k, s in var.spokes : k => s.address_space }

  spoke_subnets = merge([
    for spoke, s in var.spokes : {
      for name, cidr in s.subnets : "${spoke}/${name}" => {
        spoke = spoke
        name  = name
        cidr  = cidr
      }
    }
  ]...)
}

# ---------------- Hub ----------------
resource "azurerm_resource_group" "hub" {
  name     = "rg-${var.prefix}-connectivity"
  location = var.location
  tags     = var.tags
}

resource "azurerm_virtual_network" "hub" {
  name                = "vnet-${var.prefix}-hub"
  location            = azurerm_resource_group.hub.location
  resource_group_name = azurerm_resource_group.hub.name
  address_space       = [var.hub_address_space]
  tags                = var.tags
}

resource "azurerm_subnet" "hub" {
  for_each             = var.hub_subnets
  name                 = each.key
  resource_group_name  = azurerm_resource_group.hub.name
  virtual_network_name = azurerm_virtual_network.hub.name
  address_prefixes     = [each.value]
}

# >>> GatewaySubnet UDR: on-prem -> spokes must go through the FortiGate,
#     otherwise return traffic is asymmetric and the stateful firewall drops it.
resource "azurerm_route_table" "gateway" {
  name                = "rt-${var.prefix}-gatewaysubnet"
  location            = azurerm_resource_group.hub.location
  resource_group_name = azurerm_resource_group.hub.name
  tags                = var.tags

  dynamic "route" {
    for_each = local.spoke_prefixes
    content {
      name                   = "to-spoke-${route.key}"
      address_prefix         = route.value
      next_hop_type          = "VirtualAppliance"
      next_hop_in_ip_address = var.nva_ilb_ip
    }
  }
}

resource "azurerm_subnet_route_table_association" "gateway" {
  subnet_id      = azurerm_subnet.hub["GatewaySubnet"].id
  route_table_id = azurerm_route_table.gateway.id
}

# ---------------- Azure Bastion ----------------
# >>> No public IPs on VMs; RDP/SSH over 443 to VMs in peered spokes.
resource "azurerm_public_ip" "bastion" {
  name                = "pip-${var.prefix}-bastion"
  location            = azurerm_resource_group.hub.location
  resource_group_name = azurerm_resource_group.hub.name
  allocation_method   = "Static"
  sku                 = "Standard"
  zones               = ["1", "2", "3"]
  tags                = var.tags
}

resource "azurerm_bastion_host" "hub" {
  name                = "bas-${var.prefix}-hub"
  location            = azurerm_resource_group.hub.location
  resource_group_name = azurerm_resource_group.hub.name
  sku                 = "Standard"
  tunneling_enabled   = true # native client (az network bastion ssh)
  tags                = var.tags

  ip_configuration {
    name                 = "ipconfig"
    subnet_id            = azurerm_subnet.hub["AzureBastionSubnet"].id
    public_ip_address_id = azurerm_public_ip.bastion.id
  }
}

# ---------------- Spokes ----------------
resource "azurerm_resource_group" "spoke" {
  for_each = var.spokes
  name     = "rg-${var.prefix}-spoke-${each.key}"
  location = var.location
  tags     = var.tags
}

resource "azurerm_virtual_network" "spoke" {
  for_each            = var.spokes
  name                = "vnet-${var.prefix}-spoke-${each.key}"
  location            = azurerm_resource_group.spoke[each.key].location
  resource_group_name = azurerm_resource_group.spoke[each.key].name
  address_space       = [each.value.address_space]
  tags                = var.tags
}

resource "azurerm_subnet" "spoke" {
  for_each             = local.spoke_subnets
  name                 = each.value.name
  resource_group_name  = azurerm_resource_group.spoke[each.value.spoke].name
  virtual_network_name = azurerm_virtual_network.spoke[each.value.spoke].name
  address_prefixes     = [each.value.cidr]
}

# >>> Peering is NOT transitive. Hub offers gateway transit; spokes accept
#     forwarded traffic so the NVA can route spoke<->spoke.
resource "azurerm_virtual_network_peering" "hub_to_spoke" {
  for_each                     = var.spokes
  name                         = "peer-hub-to-${each.key}"
  resource_group_name          = azurerm_resource_group.hub.name
  virtual_network_name         = azurerm_virtual_network.hub.name
  remote_virtual_network_id    = azurerm_virtual_network.spoke[each.key].id
  allow_virtual_network_access = true
  allow_forwarded_traffic      = true
  allow_gateway_transit        = false # set true once a VPN/ER gateway exists in the hub
}

resource "azurerm_virtual_network_peering" "spoke_to_hub" {
  for_each                     = var.spokes
  name                         = "peer-${each.key}-to-hub"
  resource_group_name          = azurerm_resource_group.spoke[each.key].name
  virtual_network_name         = azurerm_virtual_network.spoke[each.key].name
  remote_virtual_network_id    = azurerm_virtual_network.hub.id
  allow_virtual_network_access = true
  allow_forwarded_traffic      = true
  use_remote_gateways          = false # set true once the hub gateway exists
}

# >>> Spoke UDR: everything to the FortiGate ILB; gateway route propagation
#     disabled so BGP-learned on-prem routes can't bypass the firewall.
resource "azurerm_route_table" "spoke" {
  for_each                      = var.spokes
  name                          = "rt-${var.prefix}-spoke-${each.key}"
  location                      = azurerm_resource_group.spoke[each.key].location
  resource_group_name           = azurerm_resource_group.spoke[each.key].name
  bgp_route_propagation_enabled = false
  tags                          = var.tags

  route {
    name                   = "default-to-fortigate"
    address_prefix         = "0.0.0.0/0"
    next_hop_type          = "VirtualAppliance"
    next_hop_in_ip_address = var.nva_ilb_ip
  }

  # Other spokes: 0/0 already covers them (spokes aren't peered to each other),
  # but explicit routes document intent and survive a future direct peering.
  dynamic "route" {
    for_each = { for k, v in local.spoke_prefixes : k => v if k != each.key }
    content {
      name                   = "to-spoke-${route.key}"
      address_prefix         = route.value
      next_hop_type          = "VirtualAppliance"
      next_hop_in_ip_address = var.nva_ilb_ip
    }
  }

  dynamic "route" {
    for_each = toset(var.onprem_prefixes)
    content {
      name                   = "to-onprem-${replace(replace(route.value, ".", "-"), "/", "_")}"
      address_prefix         = route.value
      next_hop_type          = "VirtualAppliance"
      next_hop_in_ip_address = var.nva_ilb_ip
    }
  }
}

resource "azurerm_subnet_route_table_association" "spoke" {
  for_each       = local.spoke_subnets
  subnet_id      = azurerm_subnet.spoke[each.key].id
  route_table_id = azurerm_route_table.spoke[each.value.spoke].id
}

# >>> NSG per spoke subnet: allow SSH/RDP only from Bastion, deny the broad
#     VirtualNetwork default (which includes peered VNets + on-prem).
#     Add app-specific allow rules (priority < 4000) per subnet in real use.
resource "azurerm_network_security_group" "spoke" {
  for_each            = local.spoke_subnets
  name                = "nsg-${each.value.spoke}-${each.value.name}"
  location            = azurerm_resource_group.spoke[each.value.spoke].location
  resource_group_name = azurerm_resource_group.spoke[each.value.spoke].name
  tags                = var.tags

  security_rule {
    name                       = "allow-mgmt-from-bastion"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_ranges    = ["22", "3389"]
    source_address_prefix      = var.hub_subnets["AzureBastionSubnet"]
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "allow-lb-probes"
    priority                   = 200
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "AzureLoadBalancer"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "deny-vnet-inbound"
    priority                   = 4000
    direction                  = "Inbound"
    access                     = "Deny"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "VirtualNetwork"
    destination_address_prefix = "*"
  }
}

resource "azurerm_subnet_network_security_group_association" "spoke" {
  for_each                  = local.spoke_subnets
  subnet_id                 = azurerm_subnet.spoke[each.key].id
  network_security_group_id = azurerm_network_security_group.spoke[each.key].id
}
