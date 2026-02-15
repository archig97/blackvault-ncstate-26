# backend/app/risk_engine.py

import math


class RiskEngine:
    def __init__(self, weights=None, smoothing=0.7):
        self.weights = weights or {
            "velocity": 8,
            "dispersion": 7,
            "entropy": 5,
            "drain": 9,
            "long_drift": 8,
            "micro": 6,
            "structural": 10,
            "density": 6,
            "maturity": 4,
            "behavioral_drift": 7,
            "suspicion": 1.5
        }
        self.smoothing = smoothing

    def score(self, features: dict) -> dict:
        f = lambda k: features.get(k, 0.0)

        behavioral_score = (
            self.weights["velocity"] * self._clamp(f("velocity_z"), 0, 5)
            + self.weights["dispersion"] * self._clamp(f("dispersion_z"), 0, 5)
            + self.weights["entropy"] * self._clamp(f("entropy_shift"), 0, 5)
            + self.weights["behavioral_drift"] * self._clamp(f("behavioral_drift_score"), 0, 5)
        )

        financial_score = (
            self.weights["drain"] * self._clamp(f("drain_ratio"), 0, 1)
            + self.weights["long_drift"] * self._clamp(f("long_term_drift"), 0, 1)
            + self.weights["micro"] * self._clamp(f("micro_pattern_score"), 0, 1)
        )

        structural_score = (
            self.weights["structural"] * self._clamp(f("structural_risk"), 0, 1)
            + self.weights["density"] * self._clamp(f("risk_density"), 0, 1)
        )

        suspicion_score = self.weights["suspicion"] * f("suspicion")
        maturity_penalty = self.weights["maturity"] * f("maturity_penalty")

        raw_risk = (
            behavioral_score
            + financial_score
            + structural_score
            + suspicion_score
            + maturity_penalty
        )

        previous = f("previous_risk")

        smoothed = (
            self.smoothing * previous
            + (1 - self.smoothing) * raw_risk
        )

        final_risk = self._clamp(smoothed, 0, 100)

        return {
            "risk": round(final_risk, 2),
            "flagged": final_risk >= 70,
            "reasons": self._generate_reasons(features)
        }

    def _clamp(self, value, min_val, max_val):
        return max(min_val, min(value, max_val))

    def _generate_reasons(self, features):
        reasons = []

        if features.get("velocity_z", 0) > 2:
            reasons.append("High transaction velocity deviation")

        if features.get("dispersion_z", 0) > 2:
            reasons.append("High counterparty dispersion")

        if features.get("drain_ratio", 0) > 0.5:
            reasons.append("Significant balance drain detected")

        if features.get("long_term_drift", 0) > 0.2:
            reasons.append("Long-term financial drift detected")

        if features.get("structural_risk", 0) > 0.7:
            reasons.append("Embedded in high-risk network cluster")

        if features.get("micro_pattern_score", 0) > 0.5:
            reasons.append("Structured micro-transaction pattern")

        if features.get("suspicion", 0) > 10:
            reasons.append("Accumulated long-term suspicion")

        return reasons
