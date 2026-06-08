"""Monitoring and alerting tests."""

from __future__ import annotations

from premonition.ops.alerting import AlertManager, AlertSeverity
from premonition.ops.audit_compliance import ComplianceAuditLogger


def test_drift_alert_fires():
    mgr = AlertManager()
    alert = mgr.check_drift_alert(0.35, threshold=0.2)
    assert alert is not None
    assert alert.severity == AlertSeverity.WARNING


def test_critical_drift_alert():
    mgr = AlertManager()
    alert = mgr.check_drift_alert(0.6, threshold=0.2)
    assert alert.severity == AlertSeverity.CRITICAL


def test_latency_alert():
    mgr = AlertManager()
    alert = mgr.check_latency_alert(2500, threshold_ms=2000)
    assert alert is not None


def test_alert_prometheus_export():
    mgr = AlertManager()
    mgr.check_drift_alert(0.5)
    lines = mgr.prometheus_lines()
    assert "premonition_alerts_fired_total" in lines


def test_compliance_audit_logger():
    logger = ComplianceAuditLogger()
    logger.log("admin@test", "model_promote", "t1/best_model", details={"stage": "production"})
    events = logger.query(action="model_promote")
    assert len(events) == 1
    assert events[0]["actor"] == "admin@test"
