import { useState, useEffect } from "react";
import LiveFeed from "./components/LiveFeed.jsx";
import StatsPanel from "./components/StatsPanel.jsx";
import GraphViewWrapper from "./components/GraphViewWrapper.jsx";
import ValkeyBadge from "./components/ValkeyBadge.jsx";
import { mockWebSocket } from "./utils/mockWebSocket.js";

export default function App() {
  const [transactions, setTransactions] = useState([]);
  const [newTxId, setNewTxId] = useState(null);

  // Connect to mock WebSocket on mount
  useEffect(() => {
    // Load initial batch of transactions
    const initialData = mockWebSocket.generateBatch(5);
    setTransactions(initialData);

    // Connect to WebSocket for real-time updates
    const disconnect = mockWebSocket.connect((newTx) => {
      setNewTxId(newTx.transaction.id);
      setTransactions((prev) => [newTx, ...prev].slice(0, 15));

      // Clear highlight after animation
      setTimeout(() => setNewTxId(null), 1000);
    });

    // Cleanup on unmount
    return () => {
      disconnect();
    };
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900 p-6 relative overflow-hidden">
      {/* Animated background grid */}
      <div className="absolute inset-0 bg-grid-pattern opacity-10 animate-pulse-slow"></div>

      {/* Glowing orbs */}
      <div className="absolute top-20 left-20 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl animate-float"></div>
      <div className="absolute bottom-20 right-20 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl animate-float-delayed"></div>

      <div className="max-w-7xl mx-auto relative z-10">
        {/* Epic Header */}
        <div className="mb-8 text-center">
          <div className="inline-block mb-4">
            <div className="flex items-center gap-4 bg-gradient-to-r from-cyan-500/20 via-purple-500/20 to-pink-500/20 px-8 py-4 rounded-2xl border border-cyan-500/30 backdrop-blur-sm shadow-2xl">
              <div className="text-5xl animate-pulse">🎯</div>
              <div>
                <h1 className="text-6xl font-black bg-gradient-to-r from-cyan-400 via-purple-400 to-pink-400 bg-clip-text text-transparent animate-gradient">
                  BLACKVAULT
                </h1>
                <p className="text-cyan-400 font-mono text-sm tracking-widest">THE BIG SCORE</p>
              </div>
              <div className="text-5xl animate-pulse">💰</div>
            </div>
          </div>

          <div className="flex items-center justify-center gap-4 mb-4">
            <div className="h-px w-24 bg-gradient-to-r from-transparent via-cyan-500 to-transparent"></div>
            <p className="text-gray-300 font-semibold tracking-wide">
              REAL-TIME FRAUD DETECTION POWERED BY <span className="text-red-400 font-bold">VALKEY</span>
            </p>
            <div className="h-px w-24 bg-gradient-to-r from-transparent via-cyan-500 to-transparent"></div>
          </div>

          <p className="text-gray-400 text-sm max-w-2xl mx-auto">
            Live transaction monitoring • Graph-based risk analysis • Instant threat detection
          </p>
        </div>

        <StatsPanel transactions={transactions} />
        <LiveFeed transactions={transactions} newTxId={newTxId} />
        <GraphViewWrapper transactions={transactions} />

        {/* Footer Badge */}
        <div className="mt-8 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-gray-800/50 border border-cyan-500/30 rounded-full backdrop-blur-sm">
            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
            <span className="text-xs text-gray-400 font-mono">SYSTEM ACTIVE • MONITORING IN PROGRESS</span>
          </div>
        </div>
      </div>

      {/* Valkey Badge */}
      <ValkeyBadge />
    </div>
  );
}
