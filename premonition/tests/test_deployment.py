"""Deployment validation tests — K8s manifests, Helm, Docker."""

from __future__ import annotations

from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_k8s_manifests_exist():
    k8s_dir = PROJECT_ROOT / "infra" / "k8s"
    required = [
        "namespace.yaml", "deployment.yaml", "service.yaml",
        "ingress.yaml", "hpa.yaml", "configmap.yaml", "secret.yaml",
        "pvc.yaml", "backup-cronjob.yaml",
    ]
    for name in required:
        assert (k8s_dir / name).exists(), f"Missing {name}"


def test_k8s_deployment_has_probes():
    doc = yaml.safe_load((PROJECT_ROOT / "infra" / "k8s" / "deployment.yaml").read_text())
    container = doc["spec"]["template"]["spec"]["containers"][0]
    assert "livenessProbe" in container
    assert "readinessProbe" in container


def test_k8s_hpa_scaling():
    doc = yaml.safe_load((PROJECT_ROOT / "infra" / "k8s" / "hpa.yaml").read_text())
    assert doc["spec"]["minReplicas"] >= 2
    assert doc["spec"]["maxReplicas"] >= doc["spec"]["minReplicas"]


def test_helm_chart_structure():
    chart = PROJECT_ROOT / "infra" / "helm" / "premonition"
    assert (chart / "Chart.yaml").exists()
    assert (chart / "values.yaml").exists()
    assert (chart / "templates" / "deployment.yaml").exists()


def test_github_workflows_exist():
    workflows = PROJECT_ROOT / ".github" / "workflows"
    for name in ["ci.yml", "build.yml", "cd.yml", "mlops.yml"]:
        assert (workflows / name).exists(), f"Missing workflow {name}"


def test_dockerfile_non_root():
    content = (PROJECT_ROOT / "Dockerfile").read_text()
    assert "USER premonition" in content


def test_prometheus_config_has_api_target():
    config = yaml.safe_load((PROJECT_ROOT / "infra" / "monitoring" / "prometheus.yml").read_text())
    jobs = [j["job_name"] for j in config["scrape_configs"]]
    assert "premonition-api" in jobs
