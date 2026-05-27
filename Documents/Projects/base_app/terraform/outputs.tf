output "app_url" {
  description = "Local URL for the running Podman container"
  value       = "http://127.0.0.1:${var.host_port}"
}

output "container_name" {
  description = "Podman container name"
  value       = var.app_name
}
