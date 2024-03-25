variable "container_image" {
  description = "Container image to deploy"
  default     = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
  type        = string
}

variable "container_port" {
  description = "Port of the HTTP server inside the container"
  default     = 80
  type        = number
}

variable "env" {
  description = "Environment"
  default     = "dev"
  type        = string
}

variable "app_name" {
  description = "Application name, used in the resource names"
  type        = string
}

variable "users_service_url" {
  description = "URL of the users service"
  type        = string
}

variable "google_maps_api_key" {
  description = "Google Maps API key"
  type        = string
  sensitive   = true
}
variable "payments_service_url" {
  description = "URL of the payments service"
  type        = string
}