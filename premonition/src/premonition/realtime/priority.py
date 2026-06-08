"""Patient Priority Ranking Engine."""

from __future__ import annotations

from premonition.realtime.schemas import AlertLevel, PatientMonitorState, PriorityRanking


class PriorityRankingEngine:
    """
    Rank patients by composite priority score.

    Score = risk (40%) + deterioration (30%) + alert count (20%) + confidence (10%)
    """

    CONFIDENCE_WEIGHT = {"High": 1.0, "Medium": 0.6, "Low": 0.3}

    def compute_score(self, state: PatientMonitorState) -> float:
        conf = self.CONFIDENCE_WEIGHT.get(state.confidence, 0.5)
        alert_factor = min(state.alert_count / 5.0, 1.0)
        score = (
            state.risk_score * 0.40
            + min(state.deterioration_rate * 3, 1.0) * 0.30
            + alert_factor * 0.20
            + conf * 0.10
        )
        return round(score, 4)

    def rank(self, patients: list[PatientMonitorState]) -> PriorityRanking:
        scored = []
        for p in patients:
            p.priority_score = self.compute_score(p)
            scored.append(p)

        scored.sort(key=lambda x: x.priority_score, reverse=True)
        for i, p in enumerate(scored):
            p.rank = i + 1

        critical = [
            p for p in scored
            if p.alert_level in {AlertLevel.RED, AlertLevel.BLACK}
            or p.risk_score >= 0.60
        ][:10]

        escalating = sorted(
            [p for p in scored if p.deterioration_rate >= 0.03 and p not in critical],
            key=lambda x: x.deterioration_rate,
            reverse=True,
        )[:10]

        stable = sorted(
            [p for p in scored if p.alert_level == AlertLevel.GREEN],
            key=lambda x: x.risk_score,
        )[:10]

        return PriorityRanking(critical=critical, escalating=escalating, stable=stable)
