import { useState, useEffect } from "react";

export default function GraphViewWrapper({ transactions = [] }) {
  const [GraphView, setGraphView] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (typeof window !== "undefined") {
      // dynamically import client-only component
      import("./GraphViewClient.jsx")
        .then((mod) => setGraphView(() => mod.default))
        .catch((err) => {
          console.error("Failed to load GraphViewClient:", err);
          setError(err.message);
        });
    }
  }, []);

  if (error) {
    return (
      <div className="bg-gradient-to-br from-gray-800 to-gray-900 p-6 rounded-xl shadow-2xl text-white border border-red-500/30 backdrop-blur-sm">
        <div className="flex items-center gap-3 mb-4">
          <div className="text-3xl">⚠️</div>
          <div>
            <h2 className="text-2xl font-black bg-gradient-to-r from-red-400 to-pink-400 bg-clip-text text-transparent">
              GRAPH ERROR
            </h2>
            <p className="text-xs text-gray-500 font-mono">FAILED TO LOAD COMPONENT</p>
          </div>
        </div>
        <div className="relative rounded-lg overflow-hidden border border-gray-700 p-4" style={{ backgroundColor: '#111827' }}>
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      </div>
    );
  }

  return GraphView ? (
    <GraphView transactions={transactions} />
  ) : (
    <div className="bg-gradient-to-br from-gray-800 to-gray-900 p-6 rounded-xl shadow-2xl text-white border border-purple-500/30 backdrop-blur-sm">
      <div className="flex items-center gap-3 mb-4">
        <div className="text-3xl">🕸️</div>
        <div>
          <h2 className="text-2xl font-black bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
            TRANSACTION NETWORK
          </h2>
          <p className="text-xs text-gray-500 font-mono">GRAPH-BASED RISK ANALYSIS</p>
        </div>
      </div>
      <div className="relative rounded-lg overflow-hidden border border-gray-700" style={{ backgroundColor: '#111827', height: '400px', width: '800px' }}>
        <div className="flex items-center justify-center h-full text-gray-400">Loading graph...</div>
      </div>
    </div>
  );
}
