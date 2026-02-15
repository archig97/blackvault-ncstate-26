from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .graph_api import router as graph_router
from .ingest_api import router as ingest_router

app = FastAPI(title="GraphShield")

# API routes
app.include_router(graph_router)
app.include_router(ingest_router)

# Health + root
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
