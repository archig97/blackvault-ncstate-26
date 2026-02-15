from fastapi import FastAPI
from valkey_store import ValkeyStore
from pydantic import BaseModel
import time

# Import risk engine
from risk_engine import score  # adjust if module structured differently

app = FastAPI()
store = ValkeyStore()

class Transaction(BaseModel):
    id: str
    ts: int
    sender: str
    receiver: str
    amount: float


@app.post("/tx")
def ingest_transaction(tx: Transaction):

    tx_dict = tx.dict()

    # 1️⃣ Store raw data
    store.add_transaction_to_stream(tx_dict)
    store.store_transaction_hash(tx_dict)
    store.update_graph(tx.sender, tx.receiver)
    store.update_behavior(tx_dict)

    # 2️⃣ Extract features (NEW STEP)
    features = store.extract_features(tx_dict)

    # 3️⃣ Call risk engine (NEW STEP)
    decision = score(features)

    # decision expected format:
    # {
    #   "risk": 71.3,
    #   "flagged": True,
    #   "reasons": [...]
    # }

    # 4️⃣ Store decision
    store.store_decision(
        tx.id,
        tx.sender,
        decision["risk"],
        hops=0  # optional if graph exposure not yet integrated
    )

    # 5️⃣ Return decision to frontend
    return decision


