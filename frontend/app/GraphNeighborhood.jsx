"use client";

import React, { useEffect, useState, useCallback } from "react";
import ReactFlow, { Background, Controls, MiniMap } from "reactflow";
import "reactflow/dist/style.css";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

function nodeStyle(risk, isBad) {
  if (isBad) return { border: "2px solid #d32f2f", background: "#ffebee" };
  if (risk >= 80) return { border: "2px solid #f57c00", background: "#fff3e0" };
  if (risk >= 50) return { border: "2px solid #fbc02d", background: "#fffde7" };
  if (risk > 0) return { border: "2px solid #388e3c", background: "#e8f5e9" };
  return { border: "1px solid #9e9e9e", background: "#fafafa" };
}

function layoutCircle(centerId, nodes) {
  const center = { x: 0, y: 0 };
  const others = nodes.filter((n) => n.id !== centerId);
  const radius = 260;

  const out = nodes.map((n) => ({ ...n, position: { x: 0, y: 0 } }));
  for (let i = 0; i < out.length; i++) {
    if (out[i].id === centerId) out[i].position = center;
  }

  const count = Math.max(1, others.length);
  others.forEach((n, idx) => {
    const angle = (2 * Math.PI * idx) / count;
    const pos = { x: radius * Math.cos(angle), y: radius * Math.sin(angle) };
    const k = out.findIndex((x) => x.id === n.id);
    if (k >= 0) out[k].position = pos;
  });

  return out;
}

export default function GraphNeighborhood() {
  const [nodeId, setNodeId] = useState("acct_attack");
  const [depth, setDepth] = useState(2);
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setErr("");
    try {
      const res = await fetch(
        `${API_BASE}/graph/neighborhood?node=${encodeURIComponent(nodeId)}&depth=${depth}`
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      const rawNodes = data.nodes || [];
      const rawEdges = data.edges || [];

      if (!rawNodes.some((n) => n.id === nodeId)) {
        rawNodes.push({ id: nodeId, risk: 0, is_bad: false });
      }

      const rfNodes = rawNodes.map((n) => ({
        id: n.id,
        data: { label: `${n.id}\nRisk: ${n.risk}${n.is_bad ? "\nKNOWN BAD" : ""}` },
        style: nodeStyle(n.risk || 0, !!n.is_bad),
        position: { x: 0, y: 0 },
      }));

      const rfEdges = rawEdges.map((e, i) => ({
        id: `e-${e.from}-${e.to}-${i}`,
        source: e.from,
        target: e.to,
      }));

      setNodes(layoutCircle(nodeId, rfNodes));
      setEdges(rfEdges);
    } catch (e) {
      setErr(String(e));
    } finally {
      setLoading(false);
    }
  }, [nodeId, depth]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div style={{ height: "92vh", width: "100%" }}>
      <div style={{ padding: 12, display: "flex", gap: 12, alignItems: "center" }}>
        <div>
          <div style={{ fontSize: 12, opacity: 0.7 }}>Center node</div>
          <input
            value={nodeId}
            onChange={(e) => setNodeId(e.target.value)}
            style={{ padding: 8, width: 220 }}
          />
        </div>

        <div>
          <div style={{ fontSize: 12, opacity: 0.7 }}>Depth</div>
          <select value={depth} onChange={(e) => setDepth(Number(e.target.value))} style={{ padding: 8 }}>
            <option value={1}>1</option>
            <option value={2}>2</option>
            <option value={3}>3</option>
          </select>
        </div>

        <button onClick={load} disabled={loading} style={{ padding: "8px 12px" }}>
          {loading ? "Loading…" : "Refresh"}
        </button>

        {err ? <div style={{ color: "crimson" }}>Error: {err}</div> : null}

        <div style={{ marginLeft: "auto", fontSize: 12, opacity: 0.7 }}>
          Backend: {API_BASE}
        </div>
      </div>

      <ReactFlow nodes={nodes} edges={edges} fitView>
        <MiniMap />
        <Controls />
        <Background />
      </ReactFlow>
    </div>
  );
}
