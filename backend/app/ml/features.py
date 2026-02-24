from __future__ import annotations

from typing import Dict, List

from .constants import FEATURE_ORDER


def hops_to_bad_score(hops: int) -> float:
    return 0.0 if int(hops) >= 999 else 1.0 / (1.0 + float(hops))


def vectorize_features(features: Dict) -> List[float]:
    hops = int(features.get("hops_to_bad", 999))
    merged = {**features, "hops_to_bad_score": hops_to_bad_score(hops)}
    return [float(merged.get(key, 0.0) or 0.0) for key in FEATURE_ORDER]
