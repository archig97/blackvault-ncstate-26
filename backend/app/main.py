from fastapi import FastAPI
from valkey_store import ValkeyStore
from pydantic import BaseModel
import time

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

    store.add_transaction_to_stream(tx_dict)
    store.store_transaction_hash(tx_dict)
    store.update_graph(tx.sender, tx.receiver)
    store.update_behavior(tx_dict)

    return {"status": "stored"}

@app.get("/tx/recent")
def get_recent(limit: int = 100):
    return store.get_recent(limit)


@app.get("/risk/top")
def get_top_risk(limit: int = 10):
    return store.get_top_risk(limit)


@app.get("/graph/{node}")
def get_neighbors(node: str):
    return store.get_neighbors(node)


