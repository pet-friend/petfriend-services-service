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

  products_images_container = "products"
  stores_images_container   = "stores"
}

module "microservice" {
  source = "git::https://github.com/pet-friend/terraform-microservice-module.git?ref=v2.0.8"

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

  environment_variables = {
    PRODUCTS_IMAGES_CONTAINER = local.products_images_container
    STORES_IMAGES_CONTAINER   = local.stores_images_container
    USERS_SERVICE_URL         = var.users_service_url
    PAYMENTS_SERVICE_URL      = var.payments_service_url
    GOOGLE_MAPS_API_KEY       = var.google_maps_api_key
    PAYMENTS_API_KEY          = var.payments_api_key
  }
}

data "azurerm_client_config" "config" {}

resource "azurerm_storage_container" "products_images_container" {
  name                 = local.products_images_container
  storage_account_name = module.microservice.storage_account.name
}

resource "azurerm_storage_container" "stores_images_container" {
  name                 = local.stores_images_container
  storage_account_name = module.microservice.storage_account.name
}
