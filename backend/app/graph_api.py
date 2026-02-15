from fastapi import APIRouter, Depends
from redis import Redis
from .valkey_store import ValkeyStore
from .graph_features import compute_graph_features

from .valkey import get_client
from .graph_tools import build_neighborhood, compute_hops_to_bad


router = APIRouter(prefix="/graph", tags=["graph"])

def valkey_dep() -> Redis:
    return get_client()

def store_dep(r: Redis = Depends(valkey_dep)) -> ValkeyStore:
    return ValkeyStore(r)

@router.get("/neighborhood")
def neighborhood(node: str, depth: int = 2, store: ValkeyStore = Depends(store_dep)):
    """
    Returns a subgraph around `node` up to `depth` hops (outgoing direction).
    Enriches nodes with risk + is_bad for UI.
    """
    get_neighbors = lambda n: store.r.smembers(f"nbrs:{n}")
    subgraph = build_neighborhood(node, get_neighbors, depth=depth)

    bad_nodes = set(store.r.smembers(store.BAD_NODES))

    # Fetch risks in one pipeline round-trip
    pipe = store.r.pipeline()
    for nd in subgraph["nodes"]:
        pipe.hget(store.get_node_key(nd["id"]), "risk")
    risks = pipe.execute()

    out_nodes = []
    for nd, risk in zip(subgraph["nodes"], risks):
        nid = nd["id"]
        out_nodes.append({
            "id": nid,
            "risk": int(float(risk)) if risk else 0,
            "is_bad": nid in bad_nodes,
        })

    return {"nodes": out_nodes, "edges": subgraph["edges"]}

@router.get("/hops")
def hops(node: str, store: ValkeyStore = Depends(store_dep)):
    bad_nodes = set(store.r.smembers(BAD_NODES_SET))
    get_neighbors = lambda n: store.r.smembers(f"nbrs:{n}")
    h = compute_hops_to_bad(node, get_neighbors, bad_nodes, max_depth=3)
    return {"node": node, "hops_to_bad": h}

@router.get("/features")
def features(node: str, k: int = 2, r: Redis = Depends(valkey_dep)):
    store = ValkeyStore(r)
    return compute_graph_features(node, k, store)
