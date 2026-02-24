from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List


REASON_TO_THEME = {
    "High transaction velocity deviation": "velocity burst",
    "High counterparty dispersion": "fan-out dispersion",
    "Significant balance drain detected": "balance drain",
    "Long-term financial drift detected": "long-term drift",
    "Embedded in high-risk network cluster": "network exposure",
    "Structured micro-transaction pattern": "micro-structuring",
    "Accumulated long-term suspicion": "persistent suspicion",
}


def _themes_from_reasons(reasons: List[str]) -> List[str]:
    out: List[str] = []
    for r in reasons:
        out.append(REASON_TO_THEME.get(r, r.lower()))
    return out


class NLPSummarizer:
    def summarize_account(
        self,
        account: str,
        risk: float,
        metrics: Dict[str, Any],
        reasons: List[str],
    ) -> str:
        metrics = metrics or {}
        components = (metrics or {}).get("components", {})
        inputs = (metrics or {}).get("inputs", {})
        contributions = (metrics or {}).get("contributions", {})
        final_risk = float(components.get("final_risk", risk) or risk or 0.0)
        ml_prob = float(components.get("ml_probability", 0.0) or 0.0)
        anomaly_prob = float(components.get("anomaly_probability", 0.0) or 0.0)
        model_conf = float(components.get("model_confidence", 0.0) or 0.0)

        if not reasons:
            if final_risk < 30:
                return (
                    f"{account} currently shows low anomaly pressure. "
                    "No dominant fraud pattern is active in this account."
                )
            return (
                f"{account} has elevated risk without a single dominant trigger. "
                "Continue monitoring velocity, counterparties, and network proximity."
            )

        themes = _themes_from_reasons(reasons)
        head = ", ".join(themes[:2])
        hops = int(inputs.get("hops_to_bad", 999) or 999)

        # top two weighted drivers if available
        ranked = sorted(
            [(k, float(v or 0.0)) for k, v in contributions.items()],
            key=lambda x: x[1],
            reverse=True,
        )
        top_driver_text = ""
        if ranked:
            top = [f"{k} ({v:.2f})" for k, v in ranked[:2] if v > 0]
            if top:
                top_driver_text = f" Strongest weighted drivers are {', '.join(top)}."

        if final_risk >= 80:
            severity = "critical"
        elif final_risk >= 70:
            severity = "high"
        elif final_risk >= 40:
            severity = "moderate"
        else:
            severity = "low-to-moderate"

        model_text = (
            f" ML probability is {ml_prob * 100:.1f}%"
            f" (anomaly channel {anomaly_prob * 100:.1f}%, confidence {model_conf * 100:.1f}%)."
        )

        return (
            f"{account} shows {severity} fraud risk driven by {head}. "
            f"Network proximity is {hops} hops from known bad entities, indicating elevated propagation risk.{top_driver_text}"
            f"{model_text} "
            "Recommended action: review last-hop counterparties and temporarily limit outbound transfer velocity."
        )

    def summarize_overall(self, snapshot: Dict[str, Any]) -> str:
        tx_total = int(snapshot.get("tx_total", 0) or 0)
        avg_risk = float(snapshot.get("avg_risk", 0.0) or 0.0)
        high_risk_count = int(snapshot.get("high_risk_count", 0) or 0)
        top_accounts = snapshot.get("top_accounts", []) or []

        all_reasons: List[str] = []
        for acc in top_accounts:
            all_reasons.extend(acc.get("reasons", []) or [])

        if not top_accounts:
            return (
                "No dominant bank-wide fraud trend detected yet. "
                "Continue monitoring transaction velocity, dispersion, and graph exposure."
            )

        reason_counts = Counter(all_reasons)
        top_reason, top_reason_count = (
            reason_counts.most_common(1)[0] if reason_counts else ("No dominant reason", 0)
        )
        top_theme = REASON_TO_THEME.get(top_reason, top_reason.lower())
        second_reason = reason_counts.most_common(2)[1][0] if len(reason_counts) >= 2 else None
        second_theme = REASON_TO_THEME.get(second_reason, second_reason.lower()) if second_reason else None

        top_ids = ", ".join([a.get("id", "unknown") for a in top_accounts[:3]])
        avg_ml_prob = 0.0
        if top_accounts:
            probs = []
            for a in top_accounts:
                comps = ((a.get("metrics") or {}).get("components") or {})
                probs.append(float(comps.get("ml_probability", 0.0) or 0.0))
            if probs:
                avg_ml_prob = sum(probs) / len(probs)

        pressure = "stable"
        if avg_risk >= 70 or high_risk_count >= 5:
            pressure = "elevated"
        elif avg_risk >= 40 or high_risk_count >= 2:
            pressure = "moderate"

        trend_line = f"The dominant attack trend is {top_theme} ({top_reason_count} high-risk signals)"
        if second_theme:
            trend_line += f", followed by {second_theme}"

        return (
            f"Bank-wide risk pressure is {pressure} across {tx_total} observed transactions. "
            f"{trend_line}, led by accounts {top_ids}. "
            f"Average model-estimated fraud probability among top accounts is {avg_ml_prob * 100:.1f}%. "
            "Prioritize review of these accounts and first-hop counterparties for coordinated activity."
        )
