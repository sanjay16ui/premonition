"""Resource utilization analytics."""

from __future__ import annotations

from premonition.analytics.schemas import ResourceAnalytics


class ResourceUtilizationAnalytics:
    """Staff, ventilator, and lab capacity analytics."""

    def analyze(
        self,
        icu_patients: int,
        high_risk: int,
        critical_alerts: int,
        total_beds: int = 20,
    ) -> ResourceAnalytics:
        occupancy = icu_patients / max(total_beds, 1)
        staff_util = min(occupancy * 1.2 + critical_alerts * 0.05, 1.0)
        vent_util = min(high_risk / max(icu_patients, 1) * 0.6 + occupancy * 0.3, 1.0)
        lab_util = min(high_risk * 0.08 + critical_alerts * 0.1, 1.0)

        bottlenecks = []
        if staff_util > 0.85:
            bottlenecks.append("nursing_staff")
        if vent_util > 0.75:
            bottlenecks.append("ventilators")
        if lab_util > 0.80:
            bottlenecks.append("laboratory")

        forecast = []
        for day in range(1, 8):
            factor = 1 + (day - 1) * 0.02
            forecast.append({
                "day": day,
                "staff_utilization": round(min(staff_util * factor, 1.0), 3),
                "ventilator_utilization": round(min(vent_util * factor, 1.0), 3),
                "lab_capacity": round(min(lab_util * factor, 1.0), 3),
            })

        return ResourceAnalytics(
            staff_utilization=round(staff_util, 3),
            ventilator_utilization=round(vent_util, 3),
            lab_capacity=round(lab_util, 3),
            bottleneck_resources=bottlenecks,
            forecast=forecast,
        )
