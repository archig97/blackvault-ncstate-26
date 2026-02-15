from __future__ import annotations

from collections import deque
from typing import Callable, Iterable, Dict, List, Set, Tuple, Any

GetNeighbors = Callable[[str], Iterable[str]]

def compute_hops_to_bad(
    start: str,
    get_neighbors: GetNeighbors,
    bad_nodes: Set[str],
    max_depth: int = 3,
    max_expand_per_node: int = 200,
) -> int:
    if start in bad_nodes:
        return 0

    visited: Set[str] = {start}
    q: deque[Tuple[str, int]] = deque([(start, 0)])

    while q:
        node, depth = q.popleft()
        if depth >= max_depth:
            continue

        nbrs = list(get_neighbors(node))
        if len(nbrs) > max_expand_per_node:
            nbrs = nbrs[:max_expand_per_node]

        next_depth = depth + 1
        for nb in nbrs:
            if nb in visited:
                continue
            if nb in bad_nodes:
                return next_depth
            visited.add(nb)
            q.append((nb, next_depth))

    return 999

def build_neighborhood(
    start: str,
    get_neighbors: GetNeighbors,
    depth: int = 2,
    max_nodes: int = 250,
    max_expand_per_node: int = 200,
) -> Dict[str, Any]:
    depth = max(1, min(3, depth))

    nodes: Set[str] = {start}
    edges: List[Dict[str, str]] = []

    frontier: List[str] = [start]

    for _ in range(depth):
        next_frontier: List[str] = []
        for u in frontier:
            nbrs = list(get_neighbors(u))
            if len(nbrs) > max_expand_per_node:
                nbrs = nbrs[:max_expand_per_node]

            for v in nbrs:
                edges.append({"from": u, "to": v})
                if v not in nodes:
                    nodes.add(v)
                    next_frontier.append(v)

                if len(nodes) >= max_nodes:
                    break
            if len(nodes) >= max_nodes:
                break

        if not next_frontier or len(nodes) >= max_nodes:
            break
        frontier = next_frontier

    return {"nodes": [{"id": n} for n in nodes], "edges": edges}
