from redis import Redis
import time

TX_STREAM = "tx:stream"
BAD_NODES = "bad:nodes"
RISK_RANK = "risk:rank"
ROLLING_TTL = 600  # seconds


class ValkeyStore:
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
    
    
