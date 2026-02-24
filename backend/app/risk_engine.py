from __future__ import annotations

from pathlib import Path

from .ml.constants import MODEL_NAME
from .ml.inference import load_or_train_model, predict_components


class RiskEngine:
    def __init__(self, weights=None, smoothing=0.7, blend_weights=None):
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
            "suspicion": 1.5,
        }
        self.smoothing = smoothing
        self.blend_weights = blend_weights or {"ml": 0.65, "rule": 0.35}
        self.model_name = MODEL_NAME
        self.model_path = Path(__file__).resolve().parent / "models" / "risk_hybrid_model.joblib"
        self.model = load_or_train_model(self.model_path)

    def score(self, features: dict) -> dict:
        f = lambda k: float(features.get(k, 0.0) or 0.0)
        previous = f("previous_risk")

        # Keep grouped scores for explainability/UI while final risk is ML-derived.
        velocity_c = self.weights["velocity"] * self._clamp(f("velocity_z"), 0, 5)
        dispersion_c = self.weights["dispersion"] * self._clamp(f("dispersion_z"), 0, 5)
        entropy_c = self.weights["entropy"] * self._clamp(f("entropy_shift"), 0, 5)
        behavioral_drift_c = self.weights["behavioral_drift"] * self._clamp(
            f("behavioral_drift_score"), 0, 5
        )
        behavioral_score = velocity_c + dispersion_c + entropy_c + behavioral_drift_c

        drain_c = self.weights["drain"] * self._clamp(f("drain_ratio"), 0, 1)
        long_drift_c = self.weights["long_drift"] * self._clamp(f("long_term_drift"), 0, 1)
        micro_c = self.weights["micro"] * self._clamp(f("micro_pattern_score"), 0, 1)
        financial_score = drain_c + long_drift_c + micro_c

        structural_c = self.weights["structural"] * self._clamp(f("structural_risk"), 0, 1)
        density_c = self.weights["density"] * self._clamp(f("risk_density"), 0, 1)
        structural_score = structural_c + density_c

        suspicion_score = self.weights["suspicion"] * f("suspicion")
        maturity_penalty = self.weights["maturity"] * f("maturity_penalty")

        rule_risk = self._clamp(
            behavioral_score + financial_score + structural_score + suspicion_score - maturity_penalty,
            0,
            100,
        )

        ml_out = self._predict_components(features)
        ml_probability = float(ml_out["ml_probability"])
        supervised_probability = float(ml_out["supervised_probability"])
        anomaly_probability = float(ml_out["anomaly_probability"])
        model_confidence = float(ml_out["confidence"])

        ml_risk = self._clamp(100.0 * ml_probability, 0, 100)
        blended_risk = self._clamp(
            self.blend_weights["ml"] * ml_risk
            + self.blend_weights["rule"] * rule_risk,
            0,
            100,
        )

        smoothed = self.smoothing * previous + (1 - self.smoothing) * blended_risk
        final_risk = self._clamp(smoothed, 0, 100)

        reasons = self._generate_reasons(features, ml_probability, anomaly_probability, model_confidence)

        return {
            "risk": round(final_risk, 2),
            "flagged": final_risk >= 70,
            "reasons": reasons,
            "metrics": {
                "inputs": {
                    "velocity_z": f("velocity_z"),
                    "dispersion_z": f("dispersion_z"),
                    "entropy_shift": f("entropy_shift"),
                    "drain_ratio": f("drain_ratio"),
                    "long_term_drift": f("long_term_drift"),
                    "micro_pattern_score": f("micro_pattern_score"),
                    "structural_risk": f("structural_risk"),
                    "risk_density": f("risk_density"),
                    "maturity_penalty": f("maturity_penalty"),
                    "behavioral_drift_score": f("behavioral_drift_score"),
                    "suspicion": f("suspicion"),
                    "previous_risk": previous,
                    "hops_to_bad": int(features.get("hops_to_bad", 999)),
                },
                "components": {
                    "behavioral_score": float(behavioral_score),
                    "financial_score": float(financial_score),
                    "structural_score": float(structural_score),
                    "suspicion_score": float(suspicion_score),
                    "maturity_penalty_score": float(maturity_penalty),
                    "rule_risk": float(rule_risk),
                    "ml_risk": float(ml_risk),
                    "blended_risk": float(blended_risk),
                    "raw_risk": float(blended_risk),
                    "smoothed_risk": float(smoothed),
                    "final_risk": float(final_risk),
                    "ml_probability": float(ml_probability),
                    "supervised_probability": float(supervised_probability),
                    "anomaly_probability": float(anomaly_probability),
                    "model_confidence": float(model_confidence),
                    "model": self.model_name,
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

    def _predict_components(self, features: dict) -> dict:
        try:
            return predict_components(self.model, features)
        except Exception:
            # Final fallback if model inference fails.
            v = float(features.get("velocity_z", 0) or 0)
            d = float(features.get("dispersion_z", 0) or 0)
            s = float(features.get("structural_risk", 0) or 0)
            su = float(features.get("suspicion", 0) or 0)
            h = 0.0 if int(features.get("hops_to_bad", 999)) >= 999 else 1.0 / (
                1.0 + float(features.get("hops_to_bad", 999))
            )
            heuristic = 0.08 * v + 0.07 * d + 0.35 * s + 0.03 * su + 0.15 * h
            p = self._clamp(heuristic, 0.0, 1.0)
            return {
                "supervised_probability": p,
                "anomaly_probability": p,
                "ml_probability": p,
                "confidence": float(abs(p - 0.5) * 2.0),
            }

    def _clamp(self, value, min_val, max_val):
        return max(min_val, min(value, max_val))

    def _generate_reasons(self, features, ml_probability, anomaly_probability, model_confidence):
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

        if anomaly_probability > 0.75:
            reasons.append("Unusual behavior pattern deviates from normal account population")

        if ml_probability > 0.7 and model_confidence > 0.55:
            reasons.append("ML ensemble confirms elevated composite fraud probability")

        return reasons
