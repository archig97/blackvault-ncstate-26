from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os
import time

from .valkey_store import ValkeyStore
from .graph_tools import build_neighborhood, compute_hops_to_bad
from .graph_features import compute_graph_features
from .graph_api import router as graph_router
from .risk_engine import RiskEngine
from .nlp_summarizer import NLPSummarizer

print("MAIN.PY LOADED")


class ConnectionManager:
    def __init__(self) -> None:
        self.active: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active:
            self.active.remove(websocket)

    async def broadcast(self, payload: dict) -> None:
        stale: list[WebSocket] = []
        for ws in self.active:
            try:
                await ws.send_json(payload)
            except Exception:
                stale.append(ws)
        for ws in stale:
            self.disconnect(ws)


risk_engine = RiskEngine()
store = ValkeyStore()
manager = ConnectionManager()
nlp_summarizer = NLPSummarizer()
summary_every_n_tx = max(1, int(os.getenv("THREAT_SUMMARY_EVERY_N_TX", "15")))
tx_since_summary = 0

app = FastAPI()
app.include_router(graph_router)

# CORS for UI (Next.js 3000, Vite 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    # Keep startup resilient when Valkey is not yet ready.
    try:
        store.seed_bad_node("acct_999")
    except Exception as exc:
        print(f"[startup] could not seed bad node: {exc}")


def build_ai_summary(sender: str, decision: dict) -> str:
    metrics = decision.get("metrics", {})
    reasons = decision.get("reasons", [])
    return nlp_summarizer.summarize_account(
        account=sender,
        risk=float(decision.get("risk", 0)),
        metrics=metrics,
        reasons=reasons,
    )


def build_overall_snapshot() -> dict:
    top_accounts = store.get_top_risk_accounts(10)
    recent = store.get_recent_transactions(200)
    avg_risk = 0.0
    if recent:
        avg_risk = sum(float(t.get("risk", 0) or 0) for t in recent) / float(len(recent))
    high_risk_count = sum(1 for a in top_accounts if float(a.get("risk", 0) or 0) >= 70.0)
    return {
        "tx_total": store.get_total_transactions(),
        "recent_window_size": len(recent),
        "avg_risk": avg_risk,
        "high_risk_count": high_risk_count,
        "top_accounts": [
            {
                "id": a.get("id"),
                "risk": a.get("risk"),
                "hops_to_bad": a.get("hops_to_bad"),
                "reasons": a.get("reasons", []),
                "scores": (a.get("metrics", {}) or {}).get("components", {}),
            }
            for a in top_accounts
        ],
    }


def is_legacy_tx_summary(text: str) -> bool:
    return "->" in text and "| risk" in text


def get_or_refresh_summary() -> str:
    summary = store.get_threat_summary()
    if (
        (summary == "Waiting for telemetry..." or is_legacy_tx_summary(summary))
        and store.get_total_transactions() > 0
    ):
        summary = nlp_summarizer.summarize_overall(build_overall_snapshot())
        store.set_threat_summary(summary)
    return summary


class Transaction(BaseModel):
    id: str
    ts: int
    sender: str
    receiver: str
    amount: float


class AlertUpdate(BaseModel):
    enabled: bool = True


class ReviewUpdate(BaseModel):
    action: str
    reviewer: str = "analyst"
    notes: str = ""
    snooze_hours: int = 24


@app.post("/tx")
async def ingest_transaction(tx: Transaction):
    global tx_since_summary
    tx_dict = tx.dict()
    sender = tx.sender

    # 1) Storage + graph update
    store.add_transaction_to_stream(tx_dict)
    store.store_transaction_hash(tx_dict)
    store.update_graph(tx.sender, tx.receiver)
    store.update_behavior(tx_dict)

    # 2) Behavioral features
    features = store.extract_features(tx_dict)

    # 3) Graph-derived features
    bad_nodes = set(store.r.smembers(store.BAD_NODES))
    get_neighbors = lambda n: store.r.smembers(f"nbrs:{n}")

    hops = compute_hops_to_bad(sender, get_neighbors, bad_nodes, max_depth=3)
    graph_feats = compute_graph_features(sender, store=store)

    features["hops_to_bad"] = hops
    features.update(
        {
            "structural_risk": graph_feats.get("structural_risk", 0.0),
            "risk_density": graph_feats.get("risk_density", 0.0),
        }
    )

    # 4) Risk scoring
    decision = risk_engine.score(features)
    ai_summary = build_ai_summary(sender, decision)

    # 5) Persist risk
    store.store_decision(
        tx.id,
        sender,
        decision["risk"],
        hops=hops,
        reasons=decision.get("reasons", []),
        ai_summary=ai_summary,
        metrics=decision.get("metrics", {}),
    )

    # 6) Push UI updates
    tx_event = {
        **tx_dict,
        "risk": decision["risk"],
        "flagged": decision["flagged"],
    }
    await manager.broadcast(
        {
            "type": "new_tx",
            "transaction": tx_event,
            "risk": decision["risk"],
            "account_update": {
                "id": sender,
                "risk": decision["risk"],
                "hops_to_bad": hops,
                "alert_set": store.get_account_alert(sender),
                "review": store.get_alert_case(sender),
                "reasons": decision.get("reasons", []),
                "aiSummary": ai_summary,
                "metrics": decision.get("metrics", {}),
            },
            "reasons": decision.get("reasons", []),
        }
    )

    tx_since_summary += 1
    summary = store.get_threat_summary()
    if is_legacy_tx_summary(summary):
        tx_since_summary = summary_every_n_tx

    if tx_since_summary >= summary_every_n_tx:
        snapshot = build_overall_snapshot()
        summary = nlp_summarizer.summarize_overall(snapshot)
        store.set_threat_summary(summary)
        tx_since_summary = 0

    await manager.broadcast({"type": "threat_summary", "summary": summary})

    return decision


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        summary = get_or_refresh_summary()
        await websocket.send_json(
            {
                "type": "bootstrap",
                "transactions": store.get_recent_transactions(50),
                "tx_total": store.get_total_transactions(),
                "top_accounts": store.get_top_risk_accounts(10),
                "threat_summary": summary,
            }
        )
        await websocket.send_json(
            {
                "type": "threat_summary",
                "summary": summary,
            }
        )
        while True:
            # Keep socket open; ignore client pings/messages for now.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


@app.get("/tx/recent")
def get_recent(limit: int = 100):
    return store.get_recent(limit)


@app.get("/tx/recent/enriched")
def get_recent_enriched(limit: int = 100):
    return {"transactions": store.get_recent_transactions(limit)}


@app.get("/risk/top")
def get_top_risk(limit: int = 10):
    return store.get_top_risk(limit)


@app.get("/risk/top/accounts")
def get_top_risk_accounts(limit: int = 10):
    return {"accounts": store.get_top_risk_accounts(limit)}


@app.get("/graph/{node}")
def get_neighbors(node: str):
    return store.get_neighbors(node)


@app.get("/node/{node}")
def get_node(node: str):
    return store.r.hgetall(store.get_node_key(node))


@app.get("/account/{account_id}")
def get_account_details(account_id: str):
    details = store.get_account_details(account_id)
    if details.get("metrics"):
        if not details.get("aiSummary") or details.get("aiSummary") == "No AI summary yet.":
            details["aiSummary"] = nlp_summarizer.summarize_account(
                account=account_id,
                risk=float(details.get("risk", 0)),
                metrics=details.get("metrics", {}),
                reasons=details.get("reasons", []),
            )
        if not details.get("recent_transactions"):
            details["recent_transactions"] = store.get_account_recent_transactions(
                account_id,
                limit=10,
            )
        return details

    # Fallback for old records created before metrics persistence:
    # recompute risk metrics from latest tx for this account.
    latest_tx = store.get_latest_tx_for_sender(account_id)
    if not latest_tx:
        return details

    features = store.extract_features(latest_tx)
    bad_nodes = set(store.r.smembers(store.BAD_NODES))
    get_neighbors = lambda n: store.r.smembers(f"nbrs:{n}")

    hops = compute_hops_to_bad(account_id, get_neighbors, bad_nodes, max_depth=3)
    graph_feats = compute_graph_features(account_id, store=store)
    features["hops_to_bad"] = hops
    features.update(
        {
            "structural_risk": graph_feats.get("structural_risk", 0.0),
            "risk_density": graph_feats.get("risk_density", 0.0),
        }
    )

    decision = risk_engine.score(features)
    latest_risk = float(decision.get("risk", details.get("risk", 0.0)) or 0.0)
    latest_hops = int(features.get("hops_to_bad", details.get("hops_to_bad", 999)) or 999)

    # Keep account snapshot consistent with the displayed computed metrics.
    details["risk"] = latest_risk
    details["hops_to_bad"] = latest_hops
    details["metrics"] = decision.get("metrics", {})
    if not details.get("reasons"):
        details["reasons"] = decision.get("reasons", [])
    details["aiSummary"] = nlp_summarizer.summarize_account(
        account=account_id,
        risk=float(details.get("risk", 0)),
        metrics=details.get("metrics", {}),
        reasons=details.get("reasons", []),
    )
    details["recent_transactions"] = store.get_account_recent_transactions(
        account_id,
        limit=10,
    )

    return details


@app.post("/account/{account_id}/alert")
def set_account_alert(account_id: str, body: AlertUpdate):
    store.set_account_alert(account_id, enabled=body.enabled)
    details = store.get_account_details(account_id)
    return {
        "id": account_id,
        "alert_set": details.get("alert_set", False),
        "review": details.get("review", {}),
        "risk": details.get("risk", 0.0),
    }


@app.post("/account/alert/{account_id}")
def set_account_alert_alias(account_id: str, body: AlertUpdate):
    return set_account_alert(account_id, body)


@app.post("/account/{account_id}/review")
def update_account_review(account_id: str, body: ReviewUpdate):
    action = (body.action or "").strip().lower()
    status_map = {
        "open": "OPEN",
        "under_review": "UNDER_REVIEW",
        "confirm_fraud": "CONFIRMED_FRAUD",
        "false_positive": "FALSE_POSITIVE",
        "escalate": "ESCALATED",
        "snooze": "SNOOZED",
    }
    if action not in status_map:
        return {"ok": False, "error": f"unsupported action: {body.action}"}

    status = status_map[action]
    snooze_until_ts = None
    if status == "SNOOZED":
        hrs = max(1, int(body.snooze_hours or 24))
        snooze_until_ts = int(time.time()) + hrs * 3600

    store.set_alert_case(
        account_id,
        status=status,
        reviewer=body.reviewer or "analyst",
        notes=body.notes or "",
        snooze_until_ts=snooze_until_ts,
    )

    # Couple review status with alert flag for operational safety.
    if status in ("OPEN", "UNDER_REVIEW", "CONFIRMED_FRAUD", "ESCALATED", "SNOOZED"):
        store.set_account_alert(account_id, enabled=True)
    elif status == "FALSE_POSITIVE":
        store.set_account_alert(account_id, enabled=False)

    details = store.get_account_details(account_id)
    return {
        "ok": True,
        "id": account_id,
        "alert_set": details.get("alert_set", False),
        "review": details.get("review", {}),
        "review_history": details.get("review_history", []),
        "risk": details.get("risk", 0.0),
    }


@app.post("/account/review/{account_id}")
def update_account_review_alias(account_id: str, body: ReviewUpdate):
    return update_account_review(account_id, body)


@app.get("/account/{account_id}/review")
def get_account_review(account_id: str):
    details = store.get_account_details(account_id)
    return {
        "id": account_id,
        "alert_set": details.get("alert_set", False),
        "review": details.get("review", {}),
        "review_history": details.get("review_history", []),
        "risk": details.get("risk", 0.0),
    }


@app.get("/dashboard/threat-summary")
def get_threat_summary():
    return {"summary": get_or_refresh_summary()}


@app.post("/ai/refresh-summary")
async def refresh_summary():
    summary = nlp_summarizer.summarize_overall(build_overall_snapshot())
    store.set_threat_summary(summary)
    await manager.broadcast({"type": "threat_summary", "summary": summary})
    return {"summary": summary, "provider": "nlp"}


@app.get("/dashboard/bootstrap")
def dashboard_bootstrap(
    recent_limit: int = 50,
    top_limit: int = 10,
    graph_node: str = "acct_attack",
    graph_depth: int = 2,
):
    get_neighbors = lambda n: store.r.smembers(f"nbrs:{n}")
    subgraph = build_neighborhood(graph_node, get_neighbors, depth=graph_depth)
    bad_nodes = set(store.r.smembers(store.BAD_NODES))

    nodes = []
    for nd in subgraph["nodes"]:
        nid = nd["id"]
        risk_raw = store.r.hget(store.get_node_key(nid), "risk")
        nodes.append(
            {
                "id": nid,
                "risk": float(risk_raw or 0),
                "is_bad": nid in bad_nodes,
            }
        )

    return {
        "transactions": store.get_recent_transactions(recent_limit),
        "tx_total": store.get_total_transactions(),
        "top_accounts": store.get_top_risk_accounts(top_limit),
        "threat_summary": get_or_refresh_summary(),
        "graph": {
            "nodes": nodes,
            "links": [
                {"source": e["from"], "target": e["to"]}
                for e in subgraph["edges"]
            ],
        },
    }


@app.get("/health")
def health():
    try:
        store.ping()
        valkey = "ok"
    except Exception as exc:
        valkey = f"error: {exc}"
    return {"ok": True, "valkey": valkey}


@app.get("/")
def root():
    return {"service": "GraphShield", "status": "ok", "docs": "/docs"}
