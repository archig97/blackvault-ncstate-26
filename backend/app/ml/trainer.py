from __future__ import annotations

from pathlib import Path
from time import time

import joblib
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import HistGradientBoostingClassifier, IsolationForest
from sklearn.metrics import accuracy_score, average_precision_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split

from .constants import FEATURE_ORDER, MODEL_NAME, MODEL_VERSION
from .synthetic_data import make_synthetic_dataset


def build_model(random_state: int = 42) -> HistGradientBoostingClassifier:
    return HistGradientBoostingClassifier(
        learning_rate=0.05,
        max_depth=6,
        max_iter=260,
        min_samples_leaf=40,
        random_state=random_state,
    )


def build_anomaly_model(random_state: int = 42) -> IsolationForest:
    return IsolationForest(
        n_estimators=300,
        contamination=0.08,
        random_state=random_state,
    )


def _scale_anomaly_scores(train_scores: np.ndarray, test_scores: np.ndarray):
    lo = float(np.percentile(train_scores, 5))
    hi = float(np.percentile(train_scores, 95))
    denom = max(1e-9, hi - lo)
    scaled = np.clip((test_scores - lo) / denom, 0.0, 1.0)
    return scaled, {"lo": lo, "hi": hi}


def train_and_score(model: HistGradientBoostingClassifier | None = None):
    x, y = make_synthetic_dataset()
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=42, stratify=y
    )

    base_clf = model or build_model()
    clf = CalibratedClassifierCV(base_clf, method="isotonic", cv=3)
    clf.fit(x_train, y_train)

    y_pred = clf.predict(x_test)
    y_prob_sup = clf.predict_proba(x_test)[:, 1]

    # Fit anomaly model on likely-normal traffic to better catch novel fraud regimes.
    anomaly_model = build_anomaly_model()
    normal_x = x_train[y_train == 0]
    anomaly_model.fit(normal_x if len(normal_x) > 0 else x_train)

    train_anom = -anomaly_model.score_samples(x_train)
    test_anom = -anomaly_model.score_samples(x_test)
    y_prob_anom, anomaly_scale = _scale_anomaly_scores(train_anom, test_anom)

    blend_weights = {"supervised": 0.85, "anomaly": 0.15}
    y_prob_blend = (
        blend_weights["supervised"] * y_prob_sup
        + blend_weights["anomaly"] * y_prob_anom
    )
    y_pred_blend = (y_prob_blend >= 0.5).astype(int)

    scores = {
        "accuracy_supervised": float(accuracy_score(y_test, y_pred)),
        "f1_supervised": float(f1_score(y_test, y_pred)),
        "roc_auc_supervised": float(roc_auc_score(y_test, y_prob_sup)),
        "avg_precision_supervised": float(average_precision_score(y_test, y_prob_sup)),
        "accuracy_blended": float(accuracy_score(y_test, y_pred_blend)),
        "f1_blended": float(f1_score(y_test, y_pred_blend)),
        "roc_auc_blended": float(roc_auc_score(y_test, y_prob_blend)),
        "avg_precision_blended": float(average_precision_score(y_test, y_prob_blend)),
        "support": int(len(y_test)),
    }
    artifact = {
        "model_name": MODEL_NAME,
        "model_version": MODEL_VERSION,
        "trained_at_unix": int(time()),
        "feature_order": FEATURE_ORDER,
        "supervised_model": clf,
        "anomaly_model": anomaly_model,
        "anomaly_scale": anomaly_scale,
        "blend_weights": blend_weights,
    }
    return artifact, scores


def train_score_and_save(model_path: Path):
    model_artifact, scores = train_and_score()
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model_artifact, model_path)
    return model_artifact, scores
