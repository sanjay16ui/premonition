"""Cloud deployment infrastructure validation tests."""

from __future__ import annotations

from pathlib import Path

import pytest

INFRA_ROOT = Path(__file__).resolve().parents[1] / "infra"


class TestCloudInfra:
    def test_terraform_main_exists(self):
        assert (INFRA_ROOT / "terraform" / "main.tf").exists()

    def test_terraform_variables(self):
        assert (INFRA_ROOT / "terraform" / "variables.tf").exists()

    def test_terraform_outputs(self):
        assert (INFRA_ROOT / "terraform" / "outputs.tf").exists()

    def test_aws_module(self):
        assert (INFRA_ROOT / "terraform" / "modules" / "aws" / "main.tf").exists()

    def test_azure_module(self):
        assert (INFRA_ROOT / "terraform" / "modules" / "azure" / "main.tf").exists()

    def test_gcp_module(self):
        assert (INFRA_ROOT / "terraform" / "modules" / "gcp" / "main.tf").exists()

    def test_k8s_module(self):
        assert (INFRA_ROOT / "terraform" / "modules" / "kubernetes" / "main.tf").exists()

    def test_aws_deployment_guide(self):
        assert (INFRA_ROOT / "aws" / "DEPLOYMENT_GUIDE.md").exists()

    def test_azure_deployment_guide(self):
        assert (INFRA_ROOT / "azure" / "DEPLOYMENT_GUIDE.md").exists()

    def test_gcp_deployment_guide(self):
        assert (INFRA_ROOT / "gcp" / "DEPLOYMENT_GUIDE.md").exists()

    def test_k8s_manifests(self):
        k8s = INFRA_ROOT / "k8s"
        assert (k8s / "deployment.yaml").exists()
        assert (k8s / "service.yaml").exists()
        assert (k8s / "hpa.yaml").exists()

    def test_helm_chart(self):
        assert (INFRA_ROOT / "helm" / "premonition" / "Chart.yaml").exists()

    @pytest.mark.parametrize("file", [
        "namespace.yaml", "deployment.yaml", "service.yaml",
        "ingress.yaml", "configmap.yaml", "secret.yaml", "pvc.yaml", "hpa.yaml",
    ])
    def test_k8s_files(self, file: str):
        assert (INFRA_ROOT / "k8s" / file).exists()

    def test_monitoring_config(self):
        assert (INFRA_ROOT / "monitoring" / "prometheus.yml").exists()
        assert (INFRA_ROOT / "monitoring" / "grafana-dashboard.json").exists()

    def test_terraform_cloud_providers(self):
        content = (INFRA_ROOT / "terraform" / "variables.tf").read_text()
        assert "aws" in content
        assert "azure" in content
        assert "gcp" in content
