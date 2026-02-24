from __future__ import annotations

from pathlib import Path

import joblib

from .constants import MODEL_NAME
from .features import vectorize_features
from .trainer import train_score_and_save


def load_or_train_model(model_path: Path):
    if model_path.exists():
        loaded = joblib.load(model_path)
        return loaded

    model_artifact, _ = train_score_and_save(model_path)
    return model_artifact


def predict_probability(model, features: dict) -> float:
    return float(predict_components(model, features)["ml_probability"])


def predict_components(model, features: dict) -> dict:
    x = [vectorize_features(features)]

    # Backward compatibility: plain sklearn classifier.
    if not isinstance(model, dict):
        if hasattr(model, "predict_proba"):
            p = float(model.predict_proba(x)[0][1])
            return {
                "supervised_probability": p,
                "anomaly_probability": 0.0,
                "ml_probability": p,
                "model_name": MODEL_NAME,
                "confidence": float(abs(p - 0.5) * 2.0),
            }
        pred = float(model.predict(x)[0])
        return {
            "supervised_probability": pred,
            "anomaly_probability": 0.0,
            "ml_probability": pred,
            "model_name": MODEL_NAME,
            "confidence": float(abs(pred - 0.5) * 2.0),
        }

    sup_model = model.get("supervised_model")
    anom_model = model.get("anomaly_model")
    weights = model.get("blend_weights", {"supervised": 0.85, "anomaly": 0.15})
    scale = model.get("anomaly_scale", {"lo": 0.0, "hi": 1.0})

    sup = 0.0
    if sup_model is not None and hasattr(sup_model, "predict_proba"):
        sup = float(sup_model.predict_proba(x)[0][1])

    anom = 0.0
    if anom_model is not None and hasattr(anom_model, "score_samples"):
        raw = float(-anom_model.score_samples(x)[0])
        lo = float(scale.get("lo", 0.0))
        hi = float(scale.get("hi", 1.0))
        anom = (raw - lo) / max(1e-9, (hi - lo))
        anom = max(0.0, min(1.0, anom))

    ml_probability = (
        float(weights.get("supervised", 0.85)) * sup
        + float(weights.get("anomaly", 0.15)) * anom
    )
    ml_probability = max(0.0, min(1.0, ml_probability))

    # Confidence increases when models agree and blended score is far from 0.5
    agreement = 1.0 - abs(sup - anom)
    distance = abs(ml_probability - 0.5) * 2.0
    confidence = max(0.0, min(1.0, 0.5 * agreement + 0.5 * distance))

    return {
        "supervised_probability": sup,
        "anomaly_probability": anom,
        "ml_probability": ml_probability,
        "model_name": model.get("model_name", MODEL_NAME),
        "confidence": confidence,
    }


def model_metadata() -> dict:
    return {"model": MODEL_NAME}
