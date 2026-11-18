terraform {
  required_version = ">= 1.6.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }

  # Remote state (uncomment for real use). Pipeline authenticates with OIDC.
  # backend "azurerm" {
  #   resource_group_name  = "rg-tfstate"
  #   storage_account_name = "sttfstate<unique>"
  #   container_name       = "tfstate"
  #   key                  = "connectivity/hub-spoke.tfstate"
  #   use_azuread_auth     = true
  #   use_oidc             = true
  # }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}
