from fastapi import APIRouter, Depends
from redis import Redis
from typing import Any, Dict

from .valkey import get_client
from .valkey_store import ValkeyStore
from .graph_tools import compute_hops_to_bad
from . import risk_engine

router = APIRouter(prefix="/ingest", tags=["ingest"])


def valkey_dep() -> Redis:
    return get_client()

def store_dep(r: Redis = Depends(valkey_dep)) -> ValkeyStore:
    return ValkeyStore(r)

@router.post("/tx")
def ingest_tx(tx: Dict[str, Any], store: ValkeyStore = Depends(store_dep)):
    """
    Minimal ingest endpoint:
    - persists tx + updates graph + rolling features in Valkey (Person 1)
    - computes hops_to_bad (graph feature) (Person 4)
    - scores sender risk (Person 2)
    - persists risk + leaderboard (Person 1)
    """
    store.add_transaction(tx)

    sender = str(tx.get("sender"))
    # Graph feature: hops to known bad
    bad_nodes = set(store.r.smembers("bad:nodes"))
    get_neighbors = lambda n: store.r.smembers(f"nbrs:{n}")
    hops = compute_hops_to_bad(sender, get_neighbors, bad_nodes, max_depth=3)

    # Feature store fetch + enrich with graph features
    feats = store.get_account_features(sender)
    feats["hops_to_bad"] = hops

    # Score + persist
    res = risk_engine.score(feats)
    store.set_risk(sender, float(res["risk"]))

    return {"ok": True, "sender": sender, "hops_to_bad": hops, **res}
