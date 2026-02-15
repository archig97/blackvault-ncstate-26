export default function ValkeyBadge() {
  return (
    <div className="fixed bottom-6 right-6 z-50">
      <div className="bg-gradient-to-r from-red-500/20 via-orange-500/20 to-red-500/20 backdrop-blur-md border border-red-500/50 rounded-2xl p-4 shadow-2xl hover:scale-105 transition-transform">
        <div className="flex items-center gap-3">
          <div className="text-3xl animate-pulse">⚡</div>
          <div>
            <div className="text-xs text-gray-400 uppercase tracking-wider">Powered by</div>
            <div className="text-2xl font-black bg-gradient-to-r from-red-400 to-orange-400 bg-clip-text text-transparent">
              VALKEY
            </div>
            <div className="text-xs text-gray-500 font-mono">Real-time in-memory engine</div>
          </div>
        </div>

        <div className="mt-3 pt-3 border-t border-red-500/30">
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="text-center">
              <div className="text-green-400 font-bold">⚡ INSTANT</div>
              <div className="text-gray-500">Graph Queries</div>
            </div>
            <div className="text-center">
              <div className="text-cyan-400 font-bold">🔥 LIVE</div>
              <div className="text-gray-500">Risk Scoring</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
