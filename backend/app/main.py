from fastapi import FastAPI

from .valkey_store import ValkeyStore
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from .graph_tools import compute_hops_to_bad
from .graph_features import compute_graph_features

from .graph_api import router as graph_router

import time

# Import risk engine
from .risk_engine import RiskEngine

print("MAIN.PY LOADED")

risk_engine = RiskEngine()
app = FastAPI()
app.include_router(graph_router)



store = ValkeyStore()
store.seed_bad_node("acct_999")

class Transaction(BaseModel):
    id: str
    ts: int
    sender: str
    receiver: str
    amount: float


@app.post("/tx")
def ingest_transaction(tx: Transaction):

    tx_dict = tx.dict()
    sender = tx.sender

    # 1️⃣ Storage + graph update
    store.add_transaction_to_stream(tx_dict)
    store.store_transaction_hash(tx_dict)
    store.update_graph(tx.sender, tx.receiver)
    store.update_behavior(tx_dict)

    # 2️⃣ Behavioral features
    features = store.extract_features(tx_dict)

    # 3️⃣ Graph-derived features
    bad_nodes = set(store.r.smembers(store.BAD_NODES))
    get_neighbors = lambda n: store.r.smembers(f"nbrs:{n}")

    hops = compute_hops_to_bad(
        sender,
        get_neighbors,
        bad_nodes,
        max_depth=3
    )

    graph_feats = compute_graph_features(sender, store=store)

    # Merge graph features into main feature dict
    features["hops_to_bad"] = hops
    features.update({
    "structural_risk": graph_feats.get("structural_risk", 0.0),
    "risk_density": graph_feats.get("risk_density", 0.0)
})

    # 4️⃣ Risk scoring
    decision = risk_engine.score(features)

    # 5️⃣ Persist risk
    store.store_decision(
        tx.id,
        sender,
        decision["risk"],
        hops=hops
    )

    return decision



@app.get("/tx/recent")
def get_recent(limit: int = 100):
    return store.get_recent(limit)


@app.get("/risk/top")
def get_top_risk(limit: int = 10):
    return store.get_top_risk(limit)


@app.get("/graph/{node}")
def get_neighbors(node: str):
    return store.get_neighbors(node)

@app.get("/node/{node}")
def get_node(node: str):
    return store.r.hgetall(store.get_node_key(node))

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/")
def root():
    return {"service": "GraphShield", "status": "ok", "docs": "/docs"}


# CORS for UI (Next.js 3000, Vite 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)









