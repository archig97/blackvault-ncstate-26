from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

from redis import Redis


# -----------------------------
# Key schema (single source)
# -----------------------------
RECENT_LIST_KEY = "tx:recent"                 # list of serialized tx json
BAD_NODES_SET = "bad:nodes"                   # set of known-bad accounts
RISK_LEADERBOARD_ZSET = "risk:leaderboard"    # zset account -> risk score

# Graph adjacency (outgoing)
def k_nbrs_out(acct: str) -> str:
    return f"nbrs:{acct}"

# Optional reverse adjacency (incoming)
def k_nbrs_in(acct: str) -> str:
    return f"nbrs_in:{acct}"

# Per-account stats / feature store
def k_node_hash(acct: str) -> str:
    return f"node:{acct}"

# Horizons (seconds) for TTL-based rolling counters (hackathon-friendly)
HORIZONS = {
    "1h": 60 * 60,
    "24h": 24 * 60 * 60,
    "7d": 7 * 24 * 60 * 60,
    "30d": 30 * 24 * 60 * 60,
}

def k_cnt(acct: str, horizon: str, metric: str) -> str:
    # metric examples: tx_count, amt_sum, micro_count
    return f"cnt:{horizon}:{acct}:{metric}"

def k_set(acct: str, horizon: str, metric: str) -> str:
    # metric examples: recipients
    return f"set:{horizon}:{acct}:{metric}"


@dataclass
class Tx:
    id: str
    ts: int
    type: str
    sender: str
    receiver: str
    amount: float
    currency: str = "USD"
    channel: str = "p2p"

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Tx":
        return Tx(
            id=str(d.get("id")),
            ts=int(d.get("ts", int(time.time()))),
            type=str(d.get("type", "bank")),
            sender=str(d.get("sender")),
            receiver=str(d.get("receiver")),
            amount=float(d.get("amount", 0.0)),
            currency=str(d.get("currency", "USD")),
            channel=str(d.get("channel", "p2p")),
        )


class ValkeyStore:
    """
    Person-1 module: data plane + feature store.
    No risk thresholds. No fraud decisions. No websocket.
    """

    def __init__(self, r: Redis, *, recent_max: int = 2000) -> None:
        self.r = r
        self.recent_max = recent_max

    # -----------------------------
    # Write path
    # -----------------------------
    def add_transaction(self, tx: Dict[str, Any]) -> None:
        t = Tx.from_dict(tx)
        raw = json.dumps(tx)

        # Recent feed
        pipe = self.r.pipeline()
        pipe.lpush(RECENT_LIST_KEY, raw)
        pipe.ltrim(RECENT_LIST_KEY, 0, self.recent_max - 1)

        # Persist minimal tx copy (optional)
        pipe.hset(f"tx:{t.id}", mapping={
            "id": t.id,
            "ts": t.ts,
            "type": t.type,
            "sender": t.sender,
            "receiver": t.receiver,
            "amount": t.amount,
            "currency": t.currency,
            "channel": t.channel,
        })
        pipe.expire(f"tx:{t.id}", HORIZONS["7d"])  # keep a week

        pipe.execute()

        # Graph + behavior features
        self.update_graph(t.sender, t.receiver, ts=t.ts)
        self.update_behavior(tx)

    def update_graph(self, sender: str, receiver: str, *, ts: Optional[int] = None) -> None:
        # Outgoing adjacency
        self.r.sadd(k_nbrs_out(sender), receiver)
        # Incoming adjacency (optional but helps graph richness)
        self.r.sadd(k_nbrs_in(receiver), sender)

        # Edge timestamp (for churn / last_seen)
        if ts is None:
            ts = int(time.time())
        self.r.hset(f"edge:{sender}->{receiver}", mapping={"last_ts": ts})
        self.r.expire(f"edge:{sender}->{receiver}", HORIZONS["30d"])

    def update_behavior(self, tx: Dict[str, Any]) -> None:
        t = Tx.from_dict(tx)

        # Update per-account rolling counters using TTL keys
        for horizon, ttl in HORIZONS.items():
            pipe = self.r.pipeline()

            # sender metrics
            pipe.incr(k_cnt(t.sender, horizon, "tx_count"), 1)
            pipe.incrbyfloat(k_cnt(t.sender, horizon, "amt_sum"), float(t.amount))
            pipe.sadd(k_set(t.sender, horizon, "recipients"), t.receiver)

            # receiver metrics (optional: incoming volume)
            pipe.incr(k_cnt(t.receiver, horizon, "rx_count"), 1)
            pipe.incrbyfloat(k_cnt(t.receiver, horizon, "rx_amt_sum"), float(t.amount))

            # micro-transaction heuristics
            if t.amount <= 25.0:
                pipe.incr(k_cnt(t.sender, horizon, "micro_count"), 1)

            # apply expirations
            for key in [
                k_cnt(t.sender, horizon, "tx_count"),
                k_cnt(t.sender, horizon, "amt_sum"),
                k_set(t.sender, horizon, "recipients"),
                k_cnt(t.receiver, horizon, "rx_count"),
                k_cnt(t.receiver, horizon, "rx_amt_sum"),
                k_cnt(t.sender, horizon, "micro_count"),
            ]:
                pipe.expire(key, ttl)

            pipe.execute()

        # Track "first_seen" / "last_seen" timestamps on node hash
        now = int(time.time())
        self.r.hsetnx(k_node_hash(t.sender), "first_seen", now)
        self.r.hset(k_node_hash(t.sender), mapping={"last_seen": now})
        self.r.hsetnx(k_node_hash(t.receiver), "first_seen", now)
        self.r.hset(k_node_hash(t.receiver), mapping={"last_seen": now})

    # -----------------------------
    # Read path
    # -----------------------------
    def get_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        raws = self.r.lrange(RECENT_LIST_KEY, 0, max(0, limit - 1))
        out: List[Dict[str, Any]] = []
        for s in raws:
            try:
                out.append(json.loads(s))
            except Exception:
                continue
        return out

    def get_neighbors(self, node: str, *, direction: str = "out") -> List[str]:
        if direction == "in":
            return list(self.r.smembers(k_nbrs_in(node)))
        return list(self.r.smembers(k_nbrs_out(node)))

    def get_neighbor_risks(self, node: str, *, direction: str = "out") -> Dict[str, float]:
        nbrs = self.get_neighbors(node, direction=direction)
        if not nbrs:
            return {}
        pipe = self.r.pipeline()
        for n in nbrs:
            pipe.hget(k_node_hash(n), "risk")
        vals = pipe.execute()
        out: Dict[str, float] = {}
        for n, v in zip(nbrs, vals):
            try:
                out[n] = float(v) if v is not None else 0.0
            except Exception:
                out[n] = 0.0
        return out

    def get_account_features(self, account_id: str) -> Dict[str, Any]:
        """
        Returns a feature dict that Person-2 risk_engine can score.
        Hackathon-friendly: we compute basic counts; z-scores/baselines can be added later.
        """
        features: Dict[str, Any] = {"account_id": account_id}

        # Pull rolling metrics
        for horizon in HORIZONS.keys():
            tx_count = self._get_int(k_cnt(account_id, horizon, "tx_count"))
            amt_sum = self._get_float(k_cnt(account_id, horizon, "amt_sum"))
            micro_count = self._get_int(k_cnt(account_id, horizon, "micro_count"))
            uniq_recip = self.r.scard(k_set(account_id, horizon, "recipients"))

            features[f"tx_count_{horizon}"] = tx_count
            features[f"amt_sum_{horizon}"] = amt_sum
            features[f"micro_count_{horizon}"] = micro_count
            features[f"unique_recipients_{horizon}"] = int(uniq_recip)

        # Baseline placeholders (mean/std) — can be filled by nightly jobs later
        # Keep these keys stable for the team contract.
        features.update({
            "velocity_z": 0.0,
            "dispersion_z": 0.0,
            "entropy_shift": 0.0,
            "drain_ratio": 0.0,
            "long_term_drift": 0.0,
            "micro_pattern_score": 0.0,
            "structural_risk": 0.0,
            "risk_density": 0.0,
            "maturity_penalty": 0.0,
            "behavioral_drift_score": 0.0,
            "suspicion": float(self.r.hget(k_node_hash(account_id), "suspicion") or 0.0),
            "previous_risk": float(self.r.hget(k_node_hash(account_id), "risk") or 0.0),
        })
        return features

    def update_suspicion(self, node: str, value: float) -> float:
        # store as float in node hash
        new_val = self.r.hincrbyfloat(k_node_hash(node), "suspicion", float(value))
        return float(new_val)

    def set_risk(self, node: str, risk: float) -> None:
        self.r.hset(k_node_hash(node), mapping={"risk": float(risk), "risk_updated_ts": int(time.time())})
        self.r.zadd(RISK_LEADERBOARD_ZSET, {node: float(risk)})

    def get_top_risk(self, limit: int = 10) -> List[Tuple[str, float]]:
        # highest risk first
        items = self.r.zrevrange(RISK_LEADERBOARD_ZSET, 0, max(0, limit - 1), withscores=True)
        return [(acct, float(score)) for acct, score in items]

    # -----------------------------
    # Helpers
    # -----------------------------
    def _get_int(self, key: str) -> int:
        v = self.r.get(key)
        try:
            return int(v) if v is not None else 0
        except Exception:
            return 0

    def _get_float(self, key: str) -> float:
        v = self.r.get(key)
        try:
            return float(v) if v is not None else 0.0
        except Exception:
            return 0.0
