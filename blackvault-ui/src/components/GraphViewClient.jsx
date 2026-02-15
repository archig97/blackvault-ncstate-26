import { useRef, useEffect, useMemo, useCallback, useState } from "react";

export default function GraphViewClient({ transactions = [] }) {
  const graphRef = useRef();
  const containerRef = useRef();
  const hasZoomedRef = useRef(false);
  const [ForceGraph2D, setForceGraph2D] = useState(null);
  const [loadError, setLoadError] = useState(null);

  // Load ForceGraph2D dynamically
  useEffect(() => {
    import("react-force-graph-2d")
      .then((mod) => setForceGraph2D(() => mod.default))
      .catch((err) => {
        console.error("Failed to load react-force-graph-2d:", err);
        setLoadError(err.message);
      });
  }, []);

  // Build graph data from transactions
  const data = useMemo(() => {
    if (transactions.length === 0) {
      // Default demo data
      return {
        nodes: [
          { id: "acct_1", risk: 0 },
          { id: "acct_2", risk: 0 },
          { id: "acct_3", risk: 0 },
        ],
        links: [
          { source: "acct_1", target: "acct_2" },
          { source: "acct_2", target: "acct_3" },
        ],
      };
    }

    const nodes = new Map();
    const links = [];

    transactions.forEach((tx) => {
      const sender = tx.transaction.sender;
      const receiver = tx.transaction.receiver;

      // Add sender node
      if (!nodes.has(sender)) {
        nodes.set(sender, {
          id: sender,
          risk: tx.risk_score.risk,
          structural_risk: tx.graph_metrics.structural_risk,
          suspicion: tx.advanced_metrics.suspicion_memory,
          isFraud: tx.transaction.isFraud,
        });
      } else {
        // Update with latest risk
        const existing = nodes.get(sender);
        existing.risk = Math.max(existing.risk, tx.risk_score.risk);
      }

      // Add receiver node
      if (!nodes.has(receiver)) {
        nodes.set(receiver, {
          id: receiver,
          risk: 0,
          structural_risk: 0,
          suspicion: 0,
          isFraud: 0,
        });
      }

      // Add edge
      links.push({
        source: sender,
        target: receiver,
        amount: tx.transaction.amount,
        risk: tx.risk_score.risk,
      });
    });

    return {
      nodes: Array.from(nodes.values()),
      links: links,
    };
  }, [transactions]);

  // Memoize callback functions
  const linkColor = useCallback((link) => {
    // Color links based on transaction risk
    if (link.risk > 70) {
      return 'rgba(239, 68, 68, 0.6)'; // Red for high risk
    } else if (link.risk > 40) {
      return 'rgba(245, 158, 11, 0.5)'; // Orange for medium risk
    }
    return 'rgba(6, 182, 212, 0.3)'; // Cyan for low risk
  }, []);

  const linkWidth = useCallback((link) => {
    // Thicker lines for larger transactions
    if (link.amount > 100000) return 4;
    if (link.amount > 50000) return 3;
    if (link.amount > 10000) return 2;
    return 1;
  }, []);

  const nodeCanvasObject = useCallback((node, ctx, globalScale) => {
    if (!node || !ctx || typeof node.x !== 'number' || typeof node.y !== 'number') {
      return;
    }

    try {
      // Larger, more readable sizing
      const nodeRadius = 10;
      const label = node.id ? node.id.substring(0, 12) : ''; // Truncate long IDs
      const fontSize = Math.max(10, 14/globalScale); // Minimum readable size
      ctx.font = `bold ${fontSize}px sans-serif`;
      const textWidth = ctx.measureText(label).width;
      const bckgDimensions = [textWidth + 8, fontSize + 4]; // More padding

      // Color based on risk level (from Person 2)
      let color1, color2, glowColor;
      if (node.risk > 70) {
        color1 = '#ef4444'; // red
        color2 = '#dc2626';
        glowColor = 'rgba(239, 68, 68, 0.4)';
      } else if (node.risk > 40) {
        color1 = '#f59e0b'; // orange
        color2 = '#d97706';
        glowColor = 'rgba(245, 158, 11, 0.4)';
      } else {
        color1 = '#10b981'; // green
        color2 = '#059669';
        glowColor = 'rgba(16, 185, 129, 0.4)';
      }

      // Draw glow effect for high-risk nodes
      if (node.risk > 70) {
        ctx.shadowBlur = 20;
        ctx.shadowColor = glowColor;
      }

      // Draw outer ring for fraud
      if (node.isFraud === 1) {
        ctx.strokeStyle = '#ef4444';
        ctx.lineWidth = 4;
        ctx.beginPath();
        ctx.arc(node.x, node.y, nodeRadius + 8, 0, 2 * Math.PI, false);
        ctx.stroke();
      }

      // Draw structural instability ring (from Person 4)
      if (node.structural_risk > 0.7) {
        ctx.strokeStyle = '#fbbf24';
        ctx.lineWidth = 3;
        ctx.setLineDash([5, 5]); // Dashed line
        ctx.beginPath();
        ctx.arc(node.x, node.y, nodeRadius + 5, 0, 2 * Math.PI, false);
        ctx.stroke();
        ctx.setLineDash([]); // Reset
      }

      // Draw main node circle with gradient
      const gradient = ctx.createRadialGradient(node.x, node.y, 0, node.x, node.y, nodeRadius);
      gradient.addColorStop(0, color1);
      gradient.addColorStop(1, color2);
      ctx.fillStyle = gradient;
      ctx.beginPath();
      ctx.arc(node.x, node.y, nodeRadius, 0, 2 * Math.PI, false);
      ctx.fill();

      // Add white border for better visibility
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
      ctx.lineWidth = 2;
      ctx.stroke();

      // Reset shadow
      ctx.shadowBlur = 0;

      // Draw label background with better contrast
      const labelY = node.y + nodeRadius + 8;
      ctx.fillStyle = 'rgba(17, 24, 39, 0.95)';
      ctx.strokeStyle = 'rgba(6, 182, 212, 0.5)';
      ctx.lineWidth = 1;

      // Rounded rectangle for label
      const rectX = node.x - bckgDimensions[0] / 2;
      const rectY = labelY;
      const rectWidth = bckgDimensions[0];
      const rectHeight = bckgDimensions[1];
      const radius = 4;

      ctx.beginPath();
      ctx.moveTo(rectX + radius, rectY);
      ctx.lineTo(rectX + rectWidth - radius, rectY);
      ctx.quadraticCurveTo(rectX + rectWidth, rectY, rectX + rectWidth, rectY + radius);
      ctx.lineTo(rectX + rectWidth, rectY + rectHeight - radius);
      ctx.quadraticCurveTo(rectX + rectWidth, rectY + rectHeight, rectX + rectWidth - radius, rectY + rectHeight);
      ctx.lineTo(rectX + radius, rectY + rectHeight);
      ctx.quadraticCurveTo(rectX, rectY + rectHeight, rectX, rectY + rectHeight - radius);
      ctx.lineTo(rectX, rectY + radius);
      ctx.quadraticCurveTo(rectX, rectY, rectX + radius, rectY);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();

      // Draw label text with better visibility
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillStyle = node.risk > 70 ? '#ef4444' : node.risk > 40 ? '#f59e0b' : '#10b981';
      ctx.fillText(label, node.x, labelY + bckgDimensions[1] / 2);

      // Draw risk score badge
      if (node.risk > 0) {
        const badgeY = node.y - nodeRadius - 8;
        const badgeText = `${Math.round(node.risk)}`;
        ctx.font = `bold ${fontSize * 0.8}px sans-serif`;
        const badgeWidth = ctx.measureText(badgeText).width + 6;

        // Badge background
        ctx.fillStyle = node.risk > 70 ? '#ef4444' : node.risk > 40 ? '#f59e0b' : '#10b981';
        ctx.beginPath();
        ctx.arc(node.x, badgeY, badgeWidth / 2 + 2, 0, 2 * Math.PI);
        ctx.fill();

        // Badge text
        ctx.fillStyle = '#ffffff';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(badgeText, node.x, badgeY);
      }

    } catch (err) {
      console.error('Error drawing node:', err);
    }
  }, []);

  // Prevent graph from capturing scroll events
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const preventScroll = (e) => {
      // Only prevent zoom if Ctrl/Cmd key is held
      if (!e.ctrlKey && !e.metaKey) {
        e.stopPropagation();
      }
    };

    container.addEventListener('wheel', preventScroll, { passive: false });
    return () => container.removeEventListener('wheel', preventScroll);
  }, []);

  if (loadError) {
    return (
      <div className="bg-gradient-to-br from-gray-800 to-gray-900 p-6 rounded-xl shadow-2xl text-white border border-red-500/30 backdrop-blur-sm">
        <div className="flex items-center gap-3 mb-4">
          <div className="text-3xl">⚠️</div>
          <div>
            <h2 className="text-2xl font-black bg-gradient-to-r from-red-400 to-pink-400 bg-clip-text text-transparent">
              GRAPH LIBRARY ERROR
            </h2>
            <p className="text-xs text-gray-500 font-mono">FAILED TO LOAD FORCE GRAPH</p>
          </div>
        </div>
        <div className="relative rounded-lg overflow-hidden border border-gray-700 p-4" style={{ backgroundColor: '#111827' }}>
          <p className="text-red-400 text-sm">{loadError}</p>
        </div>
      </div>
    );
  }

  if (!ForceGraph2D) {
    return (
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
          <div className="flex items-center justify-center h-full text-gray-400">Loading graph library...</div>
        </div>
      </div>
    );
  }

  return (
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

      <div
        ref={containerRef}
        className="relative rounded-lg overflow-hidden border border-gray-700"
        style={{
          cursor: 'grab',
          touchAction: 'pan-y', // Allow vertical scrolling on touch devices
          backgroundColor: '#111827', // Match the graph background to prevent white flash
          height: '500px'
        }}
      >
        <ForceGraph2D
          ref={graphRef}
          graphData={data}
          nodeLabel={(node) => `${node.id}\nRisk: ${node.risk}\nSuspicion: ${node.suspicion}`}
          backgroundColor="#111827"
          nodeRelSize={10}
          linkColor={linkColor}
          linkWidth={linkWidth}
          linkDirectionalParticles={2}
          linkDirectionalParticleWidth={2}
          linkDirectionalParticleSpeed={0.005}
          nodeCanvasObject={nodeCanvasObject}
          width={800}
          height={500}
          enableZoomInteraction={true}
          enablePanInteraction={true}
          cooldownTicks={100}
          d3AlphaDecay={0.02}
          d3VelocityDecay={0.3}
          onEngineStop={() => {
            if (!hasZoomedRef.current && graphRef.current) {
              hasZoomedRef.current = true;
              graphRef.current.zoomToFit(400, 50);
            }
          }}
        />

        {/* Legend */}
        <div className="absolute top-2 right-2 bg-gray-900/95 backdrop-blur-sm p-3 rounded-lg text-xs border border-cyan-500/30 shadow-2xl">
          <div className="font-bold text-cyan-400 mb-2">LEGEND</div>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-gradient-to-br from-green-500 to-green-600"></div>
              <span className="text-gray-300">Low Risk (0-40)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-gradient-to-br from-orange-500 to-orange-600"></div>
              <span className="text-gray-300">Medium Risk (41-70)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-gradient-to-br from-red-500 to-red-600"></div>
              <span className="text-gray-300">High Risk (71+)</span>
            </div>
            <div className="flex items-center gap-2 pt-1 border-t border-gray-700">
              <div className="w-3 h-3 rounded-full border-2 border-yellow-500" style={{borderStyle: 'dashed'}}></div>
              <span className="text-gray-300">Structural Risk</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full border-4 border-red-500"></div>
              <span className="text-gray-300">Confirmed Fraud</span>
            </div>
          </div>
        </div>

        {/* Controls hint */}
        <div className="absolute bottom-2 right-2 bg-gray-800/80 backdrop-blur-sm px-3 py-1 rounded-full text-xs text-gray-400 border border-gray-700">
          💡 Drag to pan • Scroll to zoom • Hover for details
        </div>
      </div>
    </div>
  );
}
