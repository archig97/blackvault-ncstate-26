from __future__ import annotations

from typing import Any, Dict, List


def score(features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Person-2 module: pure scoring logic.
    No Valkey access. No graph traversal. No baselines computation.
    Input: feature dict from ValkeyStore.get_account_features() + graph layer.
    Output: risk, flagged boolean, and reasons for explainability.
    """

    reasons: List[str] = []
    risk = 0.0

    # Minimal MVP scoring (hackathon-friendly)
    # You can replace weights later without changing the interface.
    tx_1h = float(features.get("tx_count_1h", 0))
    amt_1h = float(features.get("amt_sum_1h", 0.0))
    uniq_1h = float(features.get("unique_recipients_1h", 0))

    hops_to_bad = float(features.get("hops_to_bad", 999))
    risk_density = float(features.get("risk_density", 0.0))
    suspicion = float(features.get("suspicion", 0.0))

    if tx_1h >= 20:
        risk += 20
        reasons.append("High 1h transaction count")
    if uniq_1h >= 10:
        risk += 15
        reasons.append("Many unique recipients in 1h")
    if amt_1h >= 2000:
        risk += 15
        reasons.append("High 1h outgoing volume")
    if hops_to_bad <= 2:
        risk += 30
        reasons.append("Close to known bad node")
    if hops_to_bad == 3:
        risk += 15
        reasons.append("Within 3 hops of known bad node")
    if risk_density >= 0.6:
        risk += 10
        reasons.append("High-risk neighborhood density")
    if suspicion >= 10:
        risk += 10
        reasons.append("Accumulated suspicion memory")

    # Clamp and flag
    risk = max(0.0, min(100.0, risk))
    flagged = risk >= 70.0

    return {"risk": risk, "flagged": flagged, "reasons": reasons}
