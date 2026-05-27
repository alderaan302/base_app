variable "app_name" {
  description = "Name used for the Podman container and image resources"
  type        = string
  default     = "ibm-expert-labs-app"
}

variable "container_host" {
  description = "Podman API URL override. If null/empty, Terraform tries the default Podman system connection URI."
  type        = string
  default     = null
}

variable "container_port" {
  description = "Container port exposed by the app"
  type        = number
  default     = 8084
}

variable "host_port" {
  description = "Host port mapped to the container"
  type        = number
  default     = 8084
}
