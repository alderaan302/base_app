locals {
  project_root = abspath("${path.module}/..")
  image_tag    = "localhost/${var.app_name}:latest"
}

resource "null_resource" "build_app" {
  triggers = {
    dockerfile   = filesha256("${path.module}/../Dockerfile")
    requirements = filesha256("${path.module}/../requirements.txt")
    app_py       = filesha256("${path.module}/../app.py")
    index_html   = filesha256("${path.module}/../templates/index.html")
  }
  provisioner "local-exec" {
    command = "cd ${local.project_root} && podman build -t ${local.image_tag} ."
  }
}

resource "null_resource" "app" {
  triggers = {
    image_tag      = local.image_tag
    host_port      = tostring(var.host_port)
    container_port = tostring(var.container_port)
    build_trigger  = null_resource.build_app.id
    app_name       = var.app_name
  }
  provisioner "local-exec" {
    command = "podman rm -f ${var.app_name} >/dev/null 2>&1 || true && podman run -d --name ${var.app_name} -p ${var.host_port}:${var.container_port} -v ${local.project_root}/settings:/data:Z --restart unless-stopped ${local.image_tag}"
  }
  provisioner "local-exec" {
    when    = destroy
    command = "podman rm -f ${self.triggers.app_name} >/dev/null 2>&1 || true"
  }
  depends_on = [null_resource.build_app]
}
