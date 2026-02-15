import { getRiskColor, getRiskBadge, getRiskBgColor } from "../utils/riskColors.js";
import { formatTimestamp } from "../utils/mockWebSocket.js";

export default function LiveFeed({ transactions, newTxId }) {
  const isConnected = transactions.length > 0;

  return (
    <div className="bg-gradient-to-br from-gray-800 to-gray-900 p-6 rounded-xl shadow-2xl text-white mb-6 border border-cyan-500/30 backdrop-blur-sm relative overflow-hidden">
      {/* Animated scan line */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-cyan-500 to-transparent animate-scan"></div>

      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center gap-3">
          <div className="text-3xl">🔴</div>
          <div>
            <h2 className="text-2xl font-black bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
              LIVE TRANSACTION FEED
            </h2>
            <p className="text-xs text-gray-500 font-mono">VALKEY-POWERED REAL-TIME MONITORING</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1 bg-gray-900/50 border border-cyan-500/30 rounded-full">
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
            <span className="text-xs text-gray-400 font-mono">{isConnected ? 'LIVE' : 'DISCONNECTED'}</span>
          </div>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-gray-400 border-b border-gray-700">
              <th className="text-left py-3 px-2">Time</th>
              <th className="text-left py-3 px-2">Sender</th>
              <th className="text-left py-3 px-2">Receiver</th>
              <th className="text-right py-3 px-2">Amount</th>
              <th className="text-center py-3 px-2">Risk</th>
              <th className="text-center py-3 px-2">Drift</th>
              <th className="text-center py-3 px-2">Flags</th>
              <th className="text-center py-3 px-2">Activity</th>
            </tr>
          </thead>
          <tbody>
            {transactions.length === 0 && (
              <tr>
                <td colSpan="8" className="text-center py-8 text-gray-500">
                  Waiting for transactions...
                </td>
              </tr>
            )}
            {transactions.map((tx) => (
              <tr
                key={tx.transaction.id}
                className={`border-t border-gray-700/50 hover:bg-cyan-900/20 transition-all duration-300 ${
                  newTxId === tx.transaction.id ? 'bg-gradient-to-r from-cyan-500/20 via-purple-500/20 to-pink-500/20 animate-pulse border-l-4 border-l-cyan-500' : ''
                }`}
              >
                <td className="py-3 px-2 text-gray-400 text-xs font-mono">
                  {formatTimestamp(tx.transaction.timestamp)}
                </td>
                <td className="py-3 px-2 font-mono text-cyan-300 text-xs">
                  {tx.transaction.sender}
                </td>
                <td className="py-3 px-2 font-mono text-purple-300 text-xs">
                  {tx.transaction.receiver}
                </td>
                <td className="py-3 px-2 text-right font-semibold text-green-400">
                  ${parseFloat(tx.transaction.amount).toLocaleString()}
                </td>
                <td className="py-3 px-2 text-center">
                  <span className={`inline-block px-3 py-1 rounded-full text-xs font-bold ${getRiskBgColor(tx.risk_score.risk)}`}>
                    {tx.risk_score.risk}
                  </span>
                </td>
                <td className="py-3 px-2 text-center">
                  <span className={`font-mono text-xs ${
                    tx.advanced_metrics.drift_indicator > 0.5 ? 'text-red-400' :
                    tx.advanced_metrics.drift_indicator < -0.5 ? 'text-blue-400' :
                    'text-gray-400'
                  }`}>
                    {tx.advanced_metrics.drift_indicator > 0 ? '+' : ''}{tx.advanced_metrics.drift_indicator}
                  </span>
                </td>
                <td className="py-3 px-2 text-center">
                  <div className="flex gap-1 justify-center items-center">
                    {tx.ui_flags.structural_instability && (
                      <span className="px-2 py-1 bg-orange-500/20 text-orange-400 rounded text-xs border border-orange-500/50" title="Structural Instability">
                        ⚠️
                      </span>
                    )}
                    {tx.ui_flags.suspicion_trending_up && (
                      <span className="text-red-400 text-xs" title="Suspicion Trending Up">
                        ↗️
                      </span>
                    )}
                    {!tx.ui_flags.suspicion_trending_up && (
                      <span className="text-green-400 text-xs" title="Suspicion Trending Down">
                        ↘️
                      </span>
                    )}
                    {tx.ui_flags.is_zero_balance && (
                      <span className="px-2 py-1 bg-red-500/20 text-red-400 rounded text-xs border border-red-500/50" title="Account Drained">
                        💸
                      </span>
                    )}
                  </div>
                </td>
                <td className="py-3 px-2 text-center">
                  <span className={`inline-block w-16 px-2 py-1 rounded text-xs font-semibold ${
                    tx.ui_flags.activity_level === 'high' ? 'bg-red-500/20 text-red-400 border border-red-500/50' :
                    tx.ui_flags.activity_level === 'medium' ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/50' :
                    'bg-green-500/20 text-green-400 border border-green-500/50'
                  }`}>
                    {tx.ui_flags.activity_level.toUpperCase()}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="mt-4 pt-4 border-t border-cyan-500/20">
        <div className="flex flex-wrap gap-6 text-xs">
          <div className="flex items-center gap-2">
            <span className="font-bold text-cyan-400 uppercase tracking-wider">Risk Levels:</span>
            <span className="px-3 py-1 bg-green-500/20 text-green-400 rounded-full border border-green-500/50 font-semibold">0-50 LOW</span>
            <span className="px-3 py-1 bg-yellow-500/20 text-yellow-400 rounded-full border border-yellow-500/50 font-semibold">51-80 MED</span>
            <span className="px-3 py-1 bg-red-500/20 text-red-400 rounded-full border border-red-500/50 font-semibold">81-100 HIGH</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-purple-400 uppercase tracking-wider">Drift:</span>
            <span className="text-gray-400">Behavioral deviation from baseline</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-orange-400 uppercase tracking-wider">Flags:</span>
            <span className="text-gray-400">⚠️ Structural instability • ↗️↘️ Suspicion trend</span>
          </div>
        </div>
      </div>
    </div>
  );
}
