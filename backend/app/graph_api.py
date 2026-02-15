from fastapi import APIRouter, Depends
from redis import Redis
from .valkey_store import ValkeyStore
from .graph_features import compute_graph_features


from .graph_tools import build_neighborhood, compute_hops_to_bad


router = APIRouter(prefix="/graph", tags=["graph"])

store = ValkeyStore()



@router.get("/neighborhood")
def neighborhood(node: str, store, depth: int = 2):
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
def hops(node: str, store):
    bad_nodes = set(store.r.smembers(store.BAD_NODES))
    get_neighbors = lambda n: store.r.smembers(f"nbrs:{n}")
    h = compute_hops_to_bad(node, get_neighbors, bad_nodes, max_depth=3)
    return {"node": node, "hops_to_bad": h}


@router.get("/features")
def features(node: str, k: int = 2):

    gf = compute_graph_features(node, k=k, store=store)
    return gf
