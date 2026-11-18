terraform {
  required_version = ">= 1.6.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 6.0, < 8.0"
    }
  }

  # backend "gcs" {
  #   bucket = "tfstate-<org>-net"
  #   prefix = "prod/shared-vpc"
  # }
}

provider "google" {
  region = var.region
}
