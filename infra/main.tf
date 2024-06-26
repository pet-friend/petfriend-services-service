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

provider "azurerm" {
  alias = "dns_sub"
  features {}

  tenant_id       = var.dns_zone_data == null ? data.azurerm_client_config.config.tenant_id : var.dns_zone_data.tenant_id
  subscription_id = var.dns_zone_data == null ? data.azurerm_client_config.config.subscription_id : var.dns_zone_data.subscription_id
  client_id       = var.dns_zone_data == null ? data.azurerm_client_config.config.client_id : var.dns_zone_data.client_id
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
  services_images_container = "services"
}

module "microservice" {
  source = "git::https://github.com/pet-friend/terraform-microservice-module.git?ref=v3.0.1"

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
    SERVICES_IMAGES_CONTAINER = local.services_images_container
    GOOGLE_MAPS_API_KEY       = var.google_maps_api_key
    USERS_SERVICE_URL         = var.users_service_url
    NOTIFICATIONS_API_KEY     = var.notifications_api_key
    PAYMENTS_SERVICE_URL      = var.payments_service_url
    PAYMENTS_API_KEY          = var.payments_api_key
    ANIMALS_SERVICE_URL       = var.animals_service_url
  }

  providers = {
    azurerm         = azurerm
    azurerm.dns_sub = azurerm.dns_sub
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

resource "azurerm_storage_container" "services_images_container" {
  name                 = local.services_images_container
  storage_account_name = module.microservice.storage_account.name
}
