from fastapi import APIRouter, HTTPException
from redis.exceptions import RedisError
from .valkey_store import ValkeyStore
from .graph_features import compute_graph_features


from .graph_tools import build_neighborhood, compute_hops_to_bad


router = APIRouter(prefix="/graph", tags=["graph"])

store = ValkeyStore()



@router.get("/neighborhood")
def neighborhood(node: str, depth: int = 2):
    """
    Returns a subgraph around `node` up to `depth` hops (outgoing direction).
    Enriches nodes with risk + is_bad for UI.
    """
    try:
        get_neighbors = lambda n: store.r.smembers(f"nbrs:{n}")  # Using global store
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
    except RedisError as exc:
        raise HTTPException(status_code=503, detail=f"Valkey unavailable: {exc}") from exc

@router.get("/hops")
def hops(node: str):
    try:
        bad_nodes = set(store.r.smembers(store.BAD_NODES))
        get_neighbors = lambda n: store.r.smembers(f"nbrs:{n}")
        h = compute_hops_to_bad(node, get_neighbors, bad_nodes, max_depth=3)
        return {"node": node, "hops_to_bad": h}
    except RedisError as exc:
        raise HTTPException(status_code=503, detail=f"Valkey unavailable: {exc}") from exc


@router.get("/features")
def features(node: str, k: int = 2):
    try:
        gf = compute_graph_features(node, k=k, store=store)
        return gf
    except RedisError as exc:
        raise HTTPException(status_code=503, detail=f"Valkey unavailable: {exc}") from exc
