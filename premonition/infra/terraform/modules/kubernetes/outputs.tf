output "namespace" { value = kubernetes_namespace.main.metadata[0].name }
output "deployment" { value = kubernetes_deployment.api.metadata[0].name }
output "service" { value = kubernetes_service.api.metadata[0].name }
