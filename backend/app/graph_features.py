from __future__ import annotations

from collections import deque
from typing import Any, Dict, Iterable, List, Set, Tuple

from .graph_tools import compute_hops_to_bad
from .valkey_store import ValkeyStore


def _k_hop_nodes(start: str, get_neighbors, k: int, max_expand_per_node: int = 300) -> List[str]:
    """Return nodes within <=k hops (including start). Outgoing edges only."""
    if k <= 0:
        return [start]

    visited: Set[str] = {start}
    q: deque[Tuple[str, int]] = deque([(start, 0)])

    while q:
        node, depth = q.popleft()
        if depth >= k:
            continue

        nbrs = list(get_neighbors(node))
        if len(nbrs) > max_expand_per_node:
            nbrs = nbrs[:max_expand_per_node]

        nd = depth + 1
        for nb in nbrs:
            if nb in visited:
                continue
            visited.add(nb)
            q.append((nb, nd))

    return list(visited)


def compute_graph_features(node: str, k: int, store: ValkeyStore) -> Dict[str, Any]:
    """
    Person 4 (UPDATED) outputs:
      - hops_to_bad
      - risk_density (k-hop avg risk normalized 0..1)
      - max_neighbor_risk (1-hop max)
      - edge_churn_1h (uniq recipients 1h / uniq recipients 24h)
      - structural_risk (from hops_to_bad)
      - structural_instability (combo of churn + structural_risk)
    """
    r = store.r
    bad_nodes = set(r.smembers("bad:nodes"))
    get_neighbors = lambda n: r.smembers(f"nbrs:{n}")

    # 1) hops_to_bad (already in your codebase)
    hops = compute_hops_to_bad(node, get_neighbors, bad_nodes, max_depth=3)
    structural_risk = 0.0 if hops >= 999 else 1.0 / (1.0 + float(hops))

    # 2) k-hop risk density
    nodes_k = _k_hop_nodes(node, get_neighbors, k=max(1, int(k)))
    pipe = r.pipeline()
    for nid in nodes_k:
        pipe.hget(f"node:{nid}", "risk")
    risks_raw = pipe.execute()

    risks: List[float] = []
    for v in risks_raw:
        try:
            risks.append(float(v) if v is not None else 0.0)
        except Exception:
            risks.append(0.0)

    # normalize risk to 0..1 assuming risk is 0..100
    if risks:
        risk_density = sum(min(100.0, max(0.0, x)) / 100.0 for x in risks) / float(len(risks))
    else:
        risk_density = 0.0

    # 3) max 1-hop neighbor risk
    nbrs = list(get_neighbors(node))
    max_neighbor_risk = 0.0
    if nbrs:
        pipe = r.pipeline()
        for nb in nbrs:
            pipe.hget(f"node:{nb}", "risk")
        vals = pipe.execute()
        for v in vals:
            try:
                max_neighbor_risk = max(max_neighbor_risk, float(v) if v is not None else 0.0)
            except Exception:
                pass

    # 4) edge churn using your existing rolling recipient sets written by valkey_store.update_behavior()
    # keys: set:{horizon}:{acct}:recipients
    uniq_1h = int(r.scard(f"set:1h:{node}:recipients"))
    uniq_24h = int(r.scard(f"set:24h:{node}:recipients"))
    edge_churn_1h = float(uniq_1h) / float(max(1, uniq_24h))

    # 5) instability (simple + demo-friendly)
    structural_instability = 0.6 * edge_churn_1h + 0.4 * structural_risk

    return {
        "node": node,
        "k": int(k),
        "hops_to_bad": int(hops),
        "structural_risk": float(structural_risk),
        "risk_density": float(risk_density),
        "max_neighbor_risk": float(max_neighbor_risk),
        "edge_churn_1h": float(edge_churn_1h),
        "structural_instability": float(structural_instability),
        "k_hop_nodes_count": int(len(nodes_k)),
        "out_neighbors_count": int(len(nbrs)),
    }
