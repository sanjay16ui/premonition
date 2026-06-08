terraform {
  required_providers {
    kubernetes = { source = "hashicorp/kubernetes", version = "~> 2.25" }
  }
}

resource "kubernetes_namespace" "main" {
  metadata {
    name   = var.namespace
    labels = { app = var.name_prefix }
  }
}

resource "kubernetes_deployment" "api" {
  metadata {
    name      = "${var.name_prefix}-api"
    namespace = kubernetes_namespace.main.metadata[0].name
    labels    = { app = "${var.name_prefix}-api" }
  }

  spec {
    replicas = var.replicas

    selector { match_labels = { app = "${var.name_prefix}-api" } }

    template {
      metadata { labels = { app = "${var.name_prefix}-api" } }
      spec {
        container {
          name  = "api"
          image = var.image
          port { container_port = 8000 }

          env {
            name  = "PREMONITION_LOG_LEVEL"
            value = "INFO"
          }
          env {
            name  = "PREMONITION_REALTIME_ENABLED"
            value = "true"
          }

          resources {
            requests = { cpu = "500m", memory = "1Gi" }
            limits   = { cpu = "2", memory = "4Gi" }
          }

          liveness_probe {
            http_get { path = "/api/v1/health"; port = 8000 }
            initial_delay_seconds = 30
            period_seconds        = 10
          }

          readiness_probe {
            http_get { path = "/api/v1/health"; port = 8000 }
            initial_delay_seconds = 10
            period_seconds        = 5
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "api" {
  metadata {
    name      = "${var.name_prefix}-api"
    namespace = kubernetes_namespace.main.metadata[0].name
  }
  spec {
    selector = { app = "${var.name_prefix}-api" }
    port {
      port        = 80
      target_port = 8000
    }
    type = "ClusterIP"
  }
}

resource "kubernetes_horizontal_pod_autoscaler_v2" "api" {
  count = var.enable_hpa ? 1 : 0

  metadata {
    name      = "${var.name_prefix}-api-hpa"
    namespace = kubernetes_namespace.main.metadata[0].name
  }

  spec {
    scale_target_ref {
      api_version = "apps/v1"
      kind        = "Deployment"
      name        = kubernetes_deployment.api.metadata[0].name
    }
    min_replicas = var.min_replicas
    max_replicas = var.max_replicas

    metric {
      type = "Resource"
      resource {
        name = "cpu"
        target {
          type                = "Utilization"
          average_utilization = 70
        }
      }
    }
  }
}
