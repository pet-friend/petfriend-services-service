terraform {
  required_providers {
    azurerm = {
      source = "hashicorp/azurerm"
    }
    azapi = {
      source = "azure/azapi"
    }
  }
  backend "remote" {}
}

provider "azurerm" {
  features {}
}

provider "azapi" {}

locals {
  subdomain          = var.app_name
  dns_resource_group = "PRD-CENTRAL"
  dns_zone           = "petfriend.delu.ar"
  cae_resource_group = "SERVICES-RG"
  cae_name           = "SERVICES-CAE"
  db_allow_external  = false
}

module "microservice" {
  source = "git::https://github.com/pet-friend/terraform-microservice-module.git?ref=v2.0.3"

  app_name           = var.app_name
  subdomain          = local.subdomain
  dns_resource_group = local.dns_resource_group
  dns_zone           = local.dns_zone
  cae_resource_group = local.cae_resource_group
  cae_name           = local.cae_name
  db_allow_external  = local.db_allow_external

  container_image = var.container_image
  container_port  = var.container_port
  env             = var.env
}

data "azurerm_client_config" "config" {}
