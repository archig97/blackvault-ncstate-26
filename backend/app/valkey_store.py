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

        pipe.expire(cnt_key, ROLLING_TTL)
        pipe.expire(vol_key, ROLLING_TTL)
        pipe.expire(uniq_key, ROLLING_TTL)

        pipe.sadd(f"rcpt:{sender}", tx["receiver"])

        pipe.execute()

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

        self.r.zadd(RISK_RANK, {sender: risk})

    def get_recent(self, limit=100):
        return self.r.xrevrange(TX_STREAM, count=limit)
    
    def get_neighbors(self, node: str):
        return list(self.r.smembers(f"nbrs:{node}"))
    
    def get_top_risk(self, limit=10):
        return self.r.zrevrange(RISK_RANK, 0, limit-1, withscores=True)
    
    def seed_bad_node(self, node="acct_999"):
        self.r.sadd(BAD_NODES, node)

    







    

