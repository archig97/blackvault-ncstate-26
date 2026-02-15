import { useEffect, useState } from "react";

export default function StatsPanel({ transactions }) {
  const [stats, setStats] = useState({
    totalTransactions: 0,
    highRiskCount: 0,
    mediumRiskCount: 0,
    lowRiskCount: 0,
    avgRisk: 0,
    totalVolume: 0,
    flaggedCount: 0,
    structuralIssues: 0
  });

  useEffect(() => {
    if (!transactions || transactions.length === 0) return;

    const highRisk = transactions.filter(tx => tx.risk_score.risk > 80).length;
    const mediumRisk = transactions.filter(tx => tx.risk_score.risk > 50 && tx.risk_score.risk <= 80).length;
    const lowRisk = transactions.filter(tx => tx.risk_score.risk <= 50).length;
    const avgRisk = transactions.reduce((sum, tx) => sum + tx.risk_score.risk, 0) / transactions.length;
    const totalVolume = transactions.reduce((sum, tx) => sum + parseFloat(tx.transaction.amount), 0);
    const flaggedCount = transactions.filter(tx => tx.risk_score.flagged).length;
    const structuralIssues = transactions.filter(tx => tx.ui_flags.structural_instability).length;

    setStats({
      totalTransactions: transactions.length,
      highRiskCount: highRisk,
      mediumRiskCount: mediumRisk,
      lowRiskCount: lowRisk,
      avgRisk: avgRisk.toFixed(1),
      totalVolume: totalVolume.toFixed(2),
      flaggedCount,
      structuralIssues
    });
  }, [transactions]);

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      {/* Total Transactions */}
      <div className="bg-gradient-to-br from-gray-800 to-gray-900 p-4 rounded-xl border border-cyan-500/30 shadow-2xl hover:border-cyan-500/50 transition-all hover:scale-105 backdrop-blur-sm">
        <div className="text-cyan-400 text-xs uppercase mb-1 font-semibold tracking-wider">Total Transactions</div>
        <div className="text-3xl font-black text-white">{stats.totalTransactions}</div>
        <div className="text-xs text-gray-500 mt-1">↗ Live count</div>
      </div>

      {/* Average Risk */}
      <div className="bg-gradient-to-br from-gray-800 to-gray-900 p-4 rounded-xl border border-purple-500/30 shadow-2xl hover:border-purple-500/50 transition-all hover:scale-105 backdrop-blur-sm">
        <div className="text-purple-400 text-xs uppercase mb-1 font-semibold tracking-wider">Avg Risk Score</div>
        <div className={`text-3xl font-black ${
          stats.avgRisk > 80 ? 'text-red-400 animate-pulse' :
          stats.avgRisk > 50 ? 'text-yellow-400' :
          'text-green-400'
        }`}>
          {stats.avgRisk}
        </div>
        <div className="text-xs text-gray-500 mt-1">
          {stats.avgRisk > 80 ? '⚠️ Critical' : stats.avgRisk > 50 ? '⚡ Elevated' : '✓ Normal'}
        </div>
      </div>

      {/* Total Volume */}
      <div className="bg-gradient-to-br from-gray-800 to-gray-900 p-4 rounded-xl border border-green-500/30 shadow-2xl hover:border-green-500/50 transition-all hover:scale-105 backdrop-blur-sm">
        <div className="text-green-400 text-xs uppercase mb-1 font-semibold tracking-wider">Total Volume</div>
        <div className="text-3xl font-black text-green-400">
          ${parseFloat(stats.totalVolume).toLocaleString(undefined, {maximumFractionDigits: 0})}
        </div>
        <div className="text-xs text-gray-500 mt-1">💰 Monitored</div>
      </div>

      {/* Flagged Transactions */}
      <div className="bg-gradient-to-br from-gray-800 to-gray-900 p-4 rounded-xl border border-red-500/30 shadow-2xl hover:border-red-500/50 transition-all hover:scale-105 backdrop-blur-sm relative overflow-hidden">
        {stats.flaggedCount > 0 && (
          <div className="absolute inset-0 bg-red-500/5 animate-pulse"></div>
        )}
        <div className="relative">
          <div className="text-red-400 text-xs uppercase mb-1 font-semibold tracking-wider">Flagged</div>
          <div className="text-3xl font-black text-red-400">{stats.flaggedCount}</div>
          <div className="text-xs text-gray-500 mt-1">🚨 High risk</div>
        </div>
      </div>

      {/* Risk Distribution */}
      <div className="bg-gradient-to-br from-gray-800 to-gray-900 p-4 rounded-xl border border-cyan-500/30 shadow-2xl col-span-2 backdrop-blur-sm">
        <div className="text-cyan-400 text-xs uppercase mb-3 font-semibold tracking-wider">Risk Distribution</div>
        <div className="flex gap-4">
          <div className="flex-1 text-center">
            <div className="text-green-400 text-2xl font-black mb-1">{stats.lowRiskCount}</div>
            <div className="text-xs text-gray-500 uppercase">Low</div>
            <div className="mt-2 h-2 bg-gray-700 rounded-full overflow-hidden">
              <div className="h-full bg-green-500 rounded-full" style={{width: `${stats.totalTransactions > 0 ? (stats.lowRiskCount / stats.totalTransactions * 100) : 0}%`}}></div>
            </div>
          </div>
          <div className="flex-1 text-center">
            <div className="text-yellow-400 text-2xl font-black mb-1">{stats.mediumRiskCount}</div>
            <div className="text-xs text-gray-500 uppercase">Medium</div>
            <div className="mt-2 h-2 bg-gray-700 rounded-full overflow-hidden">
              <div className="h-full bg-yellow-500 rounded-full" style={{width: `${stats.totalTransactions > 0 ? (stats.mediumRiskCount / stats.totalTransactions * 100) : 0}%`}}></div>
            </div>
          </div>
          <div className="flex-1 text-center">
            <div className="text-red-400 text-2xl font-black mb-1">{stats.highRiskCount}</div>
            <div className="text-xs text-gray-500 uppercase">High</div>
            <div className="mt-2 h-2 bg-gray-700 rounded-full overflow-hidden">
              <div className="h-full bg-red-500 rounded-full" style={{width: `${stats.totalTransactions > 0 ? (stats.highRiskCount / stats.totalTransactions * 100) : 0}%`}}></div>
            </div>
          </div>
        </div>
      </div>

      {/* Structural Issues */}
      <div className="bg-gradient-to-br from-gray-800 to-gray-900 p-4 rounded-xl border border-orange-500/30 shadow-2xl col-span-2 backdrop-blur-sm">
        <div className="text-orange-400 text-xs uppercase mb-1 font-semibold tracking-wider">⚠️ Structural Instability</div>
        <div className="flex items-center gap-3">
          <div className="text-3xl font-black text-orange-400">{stats.structuralIssues}</div>
          <div className="text-sm text-gray-400">
            {stats.totalTransactions > 0
              ? `${((stats.structuralIssues / stats.totalTransactions) * 100).toFixed(1)}% of transactions`
              : '0% of transactions'}
          </div>
        </div>
      </div>
    </div>
  );
}
