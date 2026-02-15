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

        velocity_c = self.weights["velocity"] * self._clamp(f("velocity_z"), 0, 5)
        dispersion_c = self.weights["dispersion"] * self._clamp(f("dispersion_z"), 0, 5)
        entropy_c = self.weights["entropy"] * self._clamp(f("entropy_shift"), 0, 5)
        behavioral_drift_c = self.weights["behavioral_drift"] * self._clamp(
            f("behavioral_drift_score"), 0, 5
        )
        behavioral_score = (
            velocity_c
            + dispersion_c
            + entropy_c
            + behavioral_drift_c
        )

        drain_c = self.weights["drain"] * self._clamp(f("drain_ratio"), 0, 1)
        long_drift_c = self.weights["long_drift"] * self._clamp(f("long_term_drift"), 0, 1)
        micro_c = self.weights["micro"] * self._clamp(f("micro_pattern_score"), 0, 1)
        financial_score = (
            drain_c
            + long_drift_c
            + micro_c
        )

        structural_c = self.weights["structural"] * self._clamp(f("structural_risk"), 0, 1)
        density_c = self.weights["density"] * self._clamp(f("risk_density"), 0, 1)
        structural_score = (
            structural_c
            + density_c
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
        reasons = self._generate_reasons(features)

        return {
            "risk": round(final_risk, 2),
            "flagged": final_risk >= 70,
            "reasons": reasons,
            "metrics": {
                "inputs": {
                    "velocity_z": float(f("velocity_z")),
                    "dispersion_z": float(f("dispersion_z")),
                    "entropy_shift": float(f("entropy_shift")),
                    "drain_ratio": float(f("drain_ratio")),
                    "long_term_drift": float(f("long_term_drift")),
                    "micro_pattern_score": float(f("micro_pattern_score")),
                    "structural_risk": float(f("structural_risk")),
                    "risk_density": float(f("risk_density")),
                    "maturity_penalty": float(f("maturity_penalty")),
                    "behavioral_drift_score": float(f("behavioral_drift_score")),
                    "suspicion": float(f("suspicion")),
                    "previous_risk": float(previous),
                    "hops_to_bad": int(features.get("hops_to_bad", 999)),
                },
                "components": {
                    "behavioral_score": float(behavioral_score),
                    "financial_score": float(financial_score),
                    "structural_score": float(structural_score),
                    "suspicion_score": float(suspicion_score),
                    "maturity_penalty_score": float(maturity_penalty),
                    "raw_risk": float(raw_risk),
                    "smoothed_risk": float(smoothed),
                    "final_risk": float(final_risk),
                },
                "contributions": {
                    "velocity": float(velocity_c),
                    "dispersion": float(dispersion_c),
                    "entropy": float(entropy_c),
                    "behavioral_drift": float(behavioral_drift_c),
                    "drain": float(drain_c),
                    "long_drift": float(long_drift_c),
                    "micro": float(micro_c),
                    "structural": float(structural_c),
                    "density": float(density_c),
                    "suspicion": float(suspicion_score),
                },
                "reasons": reasons,
            },
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
