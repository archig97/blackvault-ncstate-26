from redis import Redis
import os
import time
import json


class ValkeyStore:

    TX_STREAM = "tx:stream"
    BAD_NODES = "bad:nodes"
    RISK_RANK = "risk:rank"
    THREAT_SUMMARY_KEY = "threat:summary"
    ROLLING_TTL = 600  # seconds

    def __init__(self, host=None, port=None):
        host = host or os.getenv("VALKEY_HOST", "localhost")
        port = int(port or os.getenv("VALKEY_PORT", "6379"))
        self.r = Redis(host=host, port=port, decode_responses=True)

    def ping(self):
        return self.r.ping()

    def get_tx_key(self, tx_id: str):
        return f"tx:{tx_id}"

    def get_node_key(self, node_id: str):
        return f"node:{node_id}"

    def get_neighbors_key(self, node: str):
        return f"nbrs:{node}"

    def get_count_key(self, node: str, bucket: str):
        return f"cnt:{node}:{bucket}"

    def get_volume_key(self, node: str, bucket: str):
        return f"vol:{node}:{bucket}"

    def get_unique_recipient_key(self, node: str, bucket: str):
        return f"uniqrcpt:{node}:{bucket}"

    def get_recipient_history_key(self, sender: str):
        return f"rcpt:{sender}"

    def add_transaction_to_stream(self, tx: dict):
        return self.r.xadd(self.TX_STREAM, tx)

    def store_transaction_hash(self, tx: dict):
        key = f"tx:{tx['id']}"
        self.r.hset(key, mapping={k: str(v) for k, v in tx.items()})

    def update_graph(self, sender: str, receiver: str):
        self.r.sadd(f"nbrs:{sender}", receiver)
        self.r.sadd(f"nbrs_in:{receiver}", sender)

    def minute_bucket(self, ts: int):
        return str(ts // 60)

    def update_behavior(self, tx: dict):
        sender = tx["sender"]
        ts = tx["ts"]
        amount = float(tx["amount"])
        bucket = self.minute_bucket(ts)

        cnt_key = f"cnt:{sender}:{bucket}"
        vol_key = f"vol:{sender}:{bucket}"
        uniq_key = f"uniqrcpt:{sender}:{bucket}"

        pipe = self.r.pipeline()
        pipe.incr(cnt_key)
        pipe.incrbyfloat(vol_key, amount)
        pipe.pfadd(uniq_key, tx["receiver"])

        pipe.expire(cnt_key, self.ROLLING_TTL)
        pipe.expire(vol_key, self.ROLLING_TTL)
        pipe.expire(uniq_key, self.ROLLING_TTL)

        pipe.sadd(f"rcpt:{sender}", tx["receiver"])

        pipe.execute()

    def extract_features(self, tx: dict) -> dict:
        """
        Extracts multi-horizon feature dictionary expected by risk_engine.score().
        This function reads from Valkey only and performs light transformations.
        """

        sender = tx["sender"]
        ts = tx["ts"]

        bucket = self.minute_bucket(ts)

        # --- Rolling Window Keys ---
        cnt_key = self.get_count_key(sender, bucket)
        vol_key = self.get_volume_key(sender, bucket)
        uniq_key = self.get_unique_recipient_key(sender, bucket)

        # --- Fetch Rolling Metrics Safely ---
        burst_count = int(self.r.get(cnt_key) or 0)
        volume = float(self.r.get(vol_key) or 0.0)
        unique_recipients = int(self.r.pfcount(uniq_key) or 0)

        # --- Previous Risk ---
        node_key = self.get_node_key(sender)
        previous_risk = float(self.r.hget(node_key, "risk") or 0.0)

        # --- Placeholder Statistical Normalization ---
        # (Replace later with true baseline + z-score computation)
        velocity_z = burst_count / 10.0
        dispersion_z = unique_recipients / 5.0
        drain_ratio = volume / 10000.0

        # --- Suspicion Composite ---
        suspicion = burst_count * 1.0 + unique_recipients * 0.5 + volume / 1000.0

        # --- Final Feature Dictionary ---
        features = {
            "velocity_z": velocity_z,
            "dispersion_z": dispersion_z,
            "entropy_shift": 0.0,  # placeholder
            "drain_ratio": drain_ratio,
            "long_term_drift": 0.0,  # placeholder
            "micro_pattern_score": 0.0,  # placeholder
            "structural_risk": 0.0,  # placeholder
            "risk_density": 0.0,  # placeholder
            "maturity_penalty": 0.0,  # placeholder
            "behavioral_drift_score": 0.0,  # placeholder
            "suspicion": suspicion,
            "previous_risk": previous_risk,
        }

        return features

    def store_decision(
        self,
        tx_id: str,
        sender: str,
        risk: float,
        hops: int,
        reasons=None,
        ai_summary: str = "",
        metrics=None,
    ):
        reasons = reasons or []
        metrics = metrics or {}
        self.r.hset(f"tx:{tx_id}", mapping={"risk": risk, "hops_to_bad": hops})

        self.r.hset(
            f"node:{sender}",
            mapping={
                "risk": risk,
                "hops_to_bad": hops,
                "last_seen_ts": int(time.time()),
                "reasons": json.dumps(reasons),
                "ai_summary": ai_summary,
                "metrics": json.dumps(metrics),
            },
        )

        self.r.zadd(self.RISK_RANK, {sender: risk})

    def get_recent(self, limit=100):
        return self.r.xrevrange(self.TX_STREAM, count=limit)

    def get_total_transactions(self) -> int:
        return int(self.r.xlen(self.TX_STREAM) or 0)

    def get_neighbors(self, node: str):
        return list(self.r.smembers(f"nbrs:{node}"))

    def get_top_risk(self, limit=10):
        return self.r.zrevrange(self.RISK_RANK, 0, limit - 1, withscores=True)

    def get_recent_transactions(self, limit=100):
        entries = self.r.xrevrange(self.TX_STREAM, count=limit)
        out = []
        for _, fields in entries:
            tx = dict(fields)
            tx_id = tx.get("id")
            tx_hash = self.r.hgetall(self.get_tx_key(tx_id)) if tx_id else {}
            tx["amount"] = float(tx.get("amount", 0) or 0)
            tx["ts"] = int(tx.get("ts", 0) or 0)
            tx["risk"] = float(tx_hash.get("risk", 0) or 0)
            tx["hops_to_bad"] = int(tx_hash.get("hops_to_bad", 999) or 999)
            out.append(tx)
        return out

    def get_account_transactions(
        self,
        account_id: str,
        *,
        suspicious_only: bool = True,
        risk_threshold: float = 70.0,
        limit: int = 100,
        scan_limit: int = 4000,
    ):
        entries = self.r.xrevrange(self.TX_STREAM, count=scan_limit)
        out = []
        for _, fields in entries:
            tx = dict(fields)
            sender = tx.get("sender")
            receiver = tx.get("receiver")
            if sender != account_id and receiver != account_id:
                continue

            tx_id = tx.get("id")
            tx_hash = self.r.hgetall(self.get_tx_key(tx_id)) if tx_id else {}
            risk = float(tx_hash.get("risk", 0) or 0)
            if suspicious_only and risk < risk_threshold:
                continue

            try:
                tx["amount"] = float(tx.get("amount", 0) or 0)
            except Exception:
                tx["amount"] = 0.0
            try:
                tx["ts"] = int(tx.get("ts", 0) or 0)
            except Exception:
                tx["ts"] = 0

            tx["risk"] = risk
            tx["hops_to_bad"] = int(tx_hash.get("hops_to_bad", 999) or 999)
            out.append(tx)

            if len(out) >= limit:
                break

        return out

    def get_account_recent_transactions(
        self,
        account_id: str,
        *,
        limit: int = 10,
        scan_limit: int = 4000,
    ):
        return self.get_account_transactions(
            account_id,
            suspicious_only=False,
            risk_threshold=0.0,
            limit=limit,
            scan_limit=scan_limit,
        )

    def set_account_alert(self, account_id: str, enabled: bool = True):
        self.r.hset(self.get_node_key(account_id), "alert_set", "1" if enabled else "0")

    def get_account_alert(self, account_id: str) -> bool:
        raw = self.r.hget(self.get_node_key(account_id), "alert_set")
        return str(raw or "0") == "1"

    def get_latest_tx_for_sender(self, sender: str, scan_limit: int = 2000):
        """
        Best-effort lookup of the latest stream tx for a sender.
        """
        entries = self.r.xrevrange(self.TX_STREAM, count=scan_limit)
        for _, fields in entries:
            tx = dict(fields)
            if tx.get("sender") != sender:
                continue
            try:
                tx["ts"] = int(tx.get("ts", 0) or 0)
            except Exception:
                tx["ts"] = 0
            try:
                tx["amount"] = float(tx.get("amount", 0) or 0)
            except Exception:
                tx["amount"] = 0.0
            if not tx.get("receiver"):
                tx["receiver"] = sender
            return tx
        return None

    def _parse_reasons(self, raw: str):
        if not raw:
            return []
        try:
            val = json.loads(raw)
            return val if isinstance(val, list) else []
        except Exception:
            return []

    def _parse_obj(self, raw: str):
        if not raw:
            return {}
        try:
            val = json.loads(raw)
            return val if isinstance(val, dict) else {}
        except Exception:
            return {}

    def get_account_details(self, account_id: str):
        node = self.r.hgetall(self.get_node_key(account_id))
        if not node:
            return {
                "id": account_id,
                "risk": 0.0,
                "hops_to_bad": 999,
                "reasons": [],
                "metrics": {},
                "aiSummary": "No telemetry yet for this account.",
            }

        return {
            "id": account_id,
            "risk": float(node.get("risk", 0) or 0),
            "hops_to_bad": int(node.get("hops_to_bad", 999) or 999),
            "alert_set": str(node.get("alert_set", "0")) == "1",
            "reasons": self._parse_reasons(node.get("reasons", "")),
            "aiSummary": node.get("ai_summary", "") or "No AI summary yet.",
            "metrics": self._parse_obj(node.get("metrics", "")),
            "last_seen_ts": int(node.get("last_seen_ts", 0) or 0),
            "out_neighbors_count": int(self.r.scard(self.get_neighbors_key(account_id))),
            "unique_recipients_total": int(self.r.scard(self.get_recipient_history_key(account_id))),
            "recent_transactions": self.get_account_recent_transactions(account_id, limit=10),
        }

    def get_top_risk_accounts(self, limit=10):
        ranked = self.get_top_risk(limit)
        out = []
        for account_id, risk in ranked:
            details = self.get_account_details(account_id)
            details["risk"] = float(risk)
            out.append(details)
        return out

    def set_threat_summary(self, summary: str):
        self.r.set(self.THREAT_SUMMARY_KEY, summary)

    def get_threat_summary(self):
        return self.r.get(self.THREAT_SUMMARY_KEY) or "Waiting for telemetry..."

    def seed_bad_node(self, node="acct_999"):
        self.r.sadd(self.BAD_NODES, node)
