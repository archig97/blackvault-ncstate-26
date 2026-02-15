from redis import Redis
import time




class ValkeyStore:

    TX_STREAM = "tx:stream"
    BAD_NODES = "bad:nodes"
    RISK_RANK = "risk:rank"
    ROLLING_TTL = 600  # seconds

    def __init__(self, host="localhost", port=6379):
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
        amount = float(tx["amount"])

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
        suspicion = (
            burst_count * 1.0 +
            unique_recipients * 0.5 +
            volume / 1000.0
        )

        # --- Final Feature Dictionary ---
        features = {
            "velocity_z": velocity_z,
            "dispersion_z": dispersion_z,
            "entropy_shift": 0.0,              # placeholder
            "drain_ratio": drain_ratio,
            "long_term_drift": 0.0,            # placeholder
            "micro_pattern_score": 0.0,        # placeholder
            "structural_risk": 0.0,            # placeholder
            "risk_density": 0.0,               # placeholder
            "maturity_penalty": 0.0,           # placeholder
            "behavioral_drift_score": 0.0,     # placeholder
            "suspicion": suspicion,
            "previous_risk": previous_risk
        }

        return features


    def store_decision(self, tx_id: str, sender: str, risk: int, hops: int):
        self.r.hset(f"tx:{tx_id}", mapping={
            "risk": risk,
            "hops_to_bad": hops
        })

        self.r.hset(f"node:{sender}", mapping={
            "risk": risk,
            "hops_to_bad": hops,
            "last_seen_ts": int(time.time())
        })

        self.r.zadd(self.RISK_RANK, {sender: risk})

    def get_recent(self, limit=100):
        return self.r.xrevrange(self.TX_STREAM, count=limit)
    
    def get_neighbors(self, node: str):
        return list(self.r.smembers(f"nbrs:{node}"))
    
    def get_top_risk(self, limit=10):
        return self.r.zrevrange(self.RISK_RANK, 0, limit-1, withscores=True)
    
    def seed_bad_node(self, node="acct_999"):
        self.r.sadd(self.BAD_NODES, node)

    







    

