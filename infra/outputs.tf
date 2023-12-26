output "container_app_default_url" {
  value = module.microservice.container_app_default_url
}

output "container_app_url" {
  value = module.microservice.container_app_url
}

output "container_app_name" {
  value = module.microservice.container_app_name
}

output "resource_group_name" {
  value = local.cae_resource_group
}

output "container_app_environment_name" {
  value = local.cae_name
}

output "db_connection_details" {
  sensitive = true
  value     = module.microservice.db_connection_details
}

output "client_id" {
  value = data.azurerm_client_config.config.client_id
}

output "tenant_id" {
  value = data.azurerm_client_config.config.tenant_id
}

output "subscription_id" {
  value = data.azurerm_client_config.config.subscription_id
}
