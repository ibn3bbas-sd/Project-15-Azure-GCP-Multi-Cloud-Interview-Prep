variable "host_project_id" {
  description = "Shared VPC host project."
  type        = string
  default     = "prod-net-host"
}

variable "service_projects" {
  description = "Service projects attached to the Shared VPC, with the subnet each may use and its deployer principal."
  type = map(object({
    subnet    = string
    principal = string # e.g. serviceAccount:deploy@app-prod.iam.gserviceaccount.com
  }))
  default = {
    app-prod = {
      subnet    = "app"
      principal = "serviceAccount:deploy@app-prod.iam.gserviceaccount.com"
    }
    data-prod = {
      subnet    = "data"
      principal = "serviceAccount:deploy@data-prod.iam.gserviceaccount.com"
    }
  }
}

variable "folder_id" {
  description = "Folder (numeric ID) where org policies are enforced."
  type        = string
  default     = "folders/000000000000"
}

variable "region" {
  type    = string
  default = "me-central2"
}

variable "subnets" {
  description = "Regional subnets with optional GKE secondary ranges."
  type = map(object({
    cidr      = string
    secondary = optional(map(string), {})
  }))
  default = {
    app = {
      cidr = "10.10.0.0/20"
      secondary = {
        pods     = "10.20.0.0/16"
        services = "10.30.0.0/20"
      }
    }
    data = {
      cidr = "10.10.16.0/20"
    }
  }
}
