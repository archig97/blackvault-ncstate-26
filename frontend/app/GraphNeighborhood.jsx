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

function toReactFlowNodes(centerId, rawNodes) {
  const normalized = (rawNodes || []).map((n) => {
    const id = String(n.id);
    const risk = Number(n.risk || 0);
    const isBad = Boolean(n.is_bad);

    return {
      id,
      data: { label: `${id}\nRisk: ${risk}${isBad ? "\nKNOWN BAD" : ""}` },
      style: nodeStyle(risk, isBad),
      position: { x: 0, y: 0 },
    };
  });

  if (!normalized.some((n) => n.id === centerId)) {
    normalized.push({
      id: centerId,
      data: { label: `${centerId}\nRisk: 0` },
      style: nodeStyle(0, false),
      position: { x: 0, y: 0 },
    });
  }

  return layoutCircle(centerId, normalized);
}

function toReactFlowEdges(rawEdges) {
  return (rawEdges || []).map((e, i) => {
    const source = String(e.from ?? e.source);
    const target = String(e.to ?? e.target);
    return {
      id: `e-${source}-${target}-${i}`,
      source,
      target,
    };
  });
}

export default function GraphNeighborhood({ graphData }) {
  const [nodeId, setNodeId] = useState("acct_attack");
  const [depth, setDepth] = useState(2);
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  // metrics state
  const [metrics, setMetrics] = useState(null);
  const [metricsErr, setMetricsErr] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setErr("");
    try {
      const res = await fetch(
        `${API_BASE}/graph/neighborhood?node=${encodeURIComponent(nodeId)}&depth=${depth}`
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      setNodes(toReactFlowNodes(nodeId, data.nodes));
      setEdges(toReactFlowEdges(data.edges));
    } catch (e) {
      setErr(String(e));
    } finally {
      setLoading(false);
    }
  }, [nodeId, depth]);

  const loadMetrics = useCallback(async () => {
    setMetricsErr("");
    try {
      const res = await fetch(
        `${API_BASE}/graph/features?node=${encodeURIComponent(nodeId)}&k=2`
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setMetrics(data);
    } catch (e) {
      setMetrics(null);
      setMetricsErr(String(e));
    }
  }, [nodeId]);

  useEffect(() => {
    load();
    loadMetrics();
  }, [load, loadMetrics]);

  const fmt = (v) => (typeof v === "number" ? v.toFixed(3) : v ?? "-");

  const incomingNodes = graphData?.nodes?.length ? toReactFlowNodes(nodeId, graphData.nodes) : nodes;
  const incomingEdges = graphData?.links?.length ? toReactFlowEdges(graphData.links) : edges;

  return (
    <div
      style={{
        minHeight: "100vh",
        width: "100%",
        padding: 16,
        color: "#e8f2ff",
        background:
          "radial-gradient(1000px 450px at 5% -5%, rgba(53,212,255,0.18), transparent 70%), radial-gradient(1000px 550px at 95% -10%, rgba(255,111,145,0.16), transparent 70%), linear-gradient(180deg, #0a1a38, #071126)",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          gap: 16,
          flexWrap: "wrap",
          marginBottom: 12,
        }}
      >
        <div>
          <div
            style={{
              display: "inline-block",
              fontSize: 12,
              fontWeight: 700,
              letterSpacing: "1px",
              textTransform: "uppercase",
              borderRadius: 999,
              padding: "6px 10px",
              background: "linear-gradient(90deg, #9aff5c, #35d4ff)",
              color: "#041324",
              marginBottom: 8,
            }}
          >
            BlackVault
          </div>
          <div style={{ fontSize: 30, fontWeight: 800, lineHeight: 1.1 }}>Network View</div>
          <div style={{ fontSize: 13, opacity: 0.78, marginTop: 6 }}>
            Live graph traversal and exposure metrics for account investigations
          </div>
        </div>

        <div />
      </div>

      <div
        style={{
          display: "grid",
          gap: 12,
          gridTemplateColumns: "1.2fr 1fr",
          marginBottom: 12,
        }}
      >
        <div
          style={{
            background: "rgba(8, 21, 46, 0.75)",
            border: "1px solid rgba(141,185,255,0.25)",
            borderRadius: 14,
            padding: 12,
          }}
        >
          <div style={{ display: "flex", gap: 10, alignItems: "end", flexWrap: "wrap" }}>
            <div>
              <div style={{ fontSize: 11, opacity: 0.72 }}>Center node</div>
              <input
                value={nodeId}
                onChange={(e) => setNodeId(e.target.value)}
                style={{
                  marginTop: 4,
                  background: "rgba(255,255,255,0.07)",
                  color: "#ecf7ff",
                  border: "1px solid rgba(255,255,255,0.2)",
                  borderRadius: 10,
                  padding: "9px 11px",
                  width: 240,
                }}
              />
            </div>

            <div>
              <div style={{ fontSize: 11, opacity: 0.72 }}>Depth</div>
              <select
                value={depth}
                onChange={(e) => setDepth(Number(e.target.value))}
                style={{
                  marginTop: 4,
                  background: "rgba(255,255,255,0.07)",
                  color: "#ecf7ff",
                  border: "1px solid rgba(255,255,255,0.2)",
                  borderRadius: 10,
                  padding: "9px 11px",
                }}
              >
                <option value={1}>1 Hop</option>
                <option value={2}>2 Hops</option>
                <option value={3}>3 Hops</option>
              </select>
            </div>

            <button
              onClick={() => { load(); loadMetrics(); }}
              disabled={loading}
              style={{
                border: "none",
                borderRadius: 10,
                padding: "10px 14px",
                color: "#fff",
                fontWeight: 700,
                cursor: "pointer",
                background: "linear-gradient(90deg, #2f7bff, #35d4ff)",
              }}
            >
              {loading ? "Loading..." : "Refresh"}
            </button>
          </div>

          {err ? (
            <div style={{ marginTop: 8, color: "#ff8dac", fontSize: 12 }}>
              Error: {err}
            </div>
          ) : null}
        </div>

        <div
          style={{
            background: "rgba(8, 21, 46, 0.75)",
            border: "1px solid rgba(141,185,255,0.25)",
            borderRadius: 14,
            padding: 12,
          }}
        >
          <div style={{ fontSize: 12, marginBottom: 8, opacity: 0.78 }}>Legend</div>
          <div style={{ display: "grid", gap: 6, fontSize: 13 }}>
            <div><span style={{ color: "#d32f2f", fontWeight: 700 }}>Known bad</span> node in red border</div>
            <div><span style={{ color: "#f57c00", fontWeight: 700 }}>High risk</span> (80+) in orange</div>
            <div><span style={{ color: "#fbc02d", fontWeight: 700 }}>Medium risk</span> (50+) in yellow</div>
            <div><span style={{ color: "#388e3c", fontWeight: 700 }}>Low risk</span> {"(>0)"} in green</div>
          </div>
        </div>
      </div>

      <div
        style={{
          display: "grid",
          gap: 10,
          gridTemplateColumns: "repeat(4, minmax(140px, 1fr))",
          marginBottom: 12,
        }}
      >
        <div style={{ background: "rgba(8,21,46,0.75)", border: "1px solid rgba(141,185,255,0.25)", borderRadius: 12, padding: 10 }}>
          <div style={{ fontSize: 11, opacity: 0.7 }}>Hops to bad</div>
          <div style={{ fontSize: 24, fontWeight: 800 }}>{metrics?.hops_to_bad ?? "-"}</div>
        </div>
        <div style={{ background: "rgba(8,21,46,0.75)", border: "1px solid rgba(141,185,255,0.25)", borderRadius: 12, padding: 10 }}>
          <div style={{ fontSize: 11, opacity: 0.7 }}>Structural risk</div>
          <div style={{ fontSize: 24, fontWeight: 800 }}>{fmt(metrics?.structural_risk)}</div>
        </div>
        <div style={{ background: "rgba(8,21,46,0.75)", border: "1px solid rgba(141,185,255,0.25)", borderRadius: 12, padding: 10 }}>
          <div style={{ fontSize: 11, opacity: 0.7 }}>Risk density</div>
          <div style={{ fontSize: 24, fontWeight: 800 }}>{fmt(metrics?.risk_density)}</div>
        </div>
        <div style={{ background: "rgba(8,21,46,0.75)", border: "1px solid rgba(141,185,255,0.25)", borderRadius: 12, padding: 10 }}>
          <div style={{ fontSize: 11, opacity: 0.7 }}>Out neighbors</div>
          <div style={{ fontSize: 24, fontWeight: 800 }}>{metrics?.out_neighbors_count ?? "-"}</div>
        </div>
      </div>

      <div
        style={{
          marginBottom: 12,
          background: "rgba(8, 21, 46, 0.75)",
          border: "1px solid rgba(141,185,255,0.25)",
          borderRadius: 14,
          padding: 12,
        }}
      >
        <div style={{ fontSize: 12, opacity: 0.78, marginBottom: 8 }}>Graph-derived metrics (P4)</div>
        {metricsErr ? (
          <div style={{ color: "#ff8dac", fontSize: 12 }}>metrics error: {metricsErr}</div>
        ) : metrics ? (
          <div style={{ fontSize: 13, display: "grid", gridTemplateColumns: "200px 1fr", rowGap: 6 }}>
            <div><b>hops_to_bad</b></div><div>{metrics.hops_to_bad}</div>
            <div><b>risk_density</b></div><div>{fmt(metrics.risk_density)}</div>
            <div><b>max_neighbor_risk</b></div><div>{fmt(metrics.max_neighbor_risk)}</div>
            <div><b>edge_churn_1h</b></div><div>{fmt(metrics.edge_churn_1h)}</div>
            <div><b>structural_risk</b></div><div>{fmt(metrics.structural_risk)}</div>
            <div><b>structural_instability</b></div><div>{fmt(metrics.structural_instability)}</div>
            <div><b>k_hop_nodes_count</b></div><div>{metrics.k_hop_nodes_count}</div>
            <div><b>out_neighbors_count</b></div><div>{metrics.out_neighbors_count}</div>
          </div>
        ) : (
          <div style={{ fontSize: 12, opacity: 0.7 }}>No metrics yet (try Refresh).</div>
        )}
      </div>

      <div
        style={{
          height: "58vh",
          borderRadius: 14,
          overflow: "hidden",
          border: "1px solid rgba(141,185,255,0.3)",
          background: "rgba(5,16,36,0.85)",
        }}
      >
        <ReactFlow nodes={incomingNodes} edges={incomingEdges} fitView>
          <MiniMap />
          <Controls />
          <Background />
        </ReactFlow>
      </div>
    </div>
  );
}
