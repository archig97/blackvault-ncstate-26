import { useState, useEffect } from "react";

export default function GraphView() {
  const [ForceGraph2D, setForceGraph2D] = useState(null);

  // Only import in browser
  useEffect(() => {
    if (typeof window !== "undefined") {
      import("react-force-graph-2d").then((mod) => {
        setForceGraph2D(() => mod.default);
      });
    }
  }, []);

  const data = {
    nodes: [
      { id: "acct_1" },
      { id: "acct_2" },
      { id: "acct_3" },
    ],
    links: [
      { source: "acct_1", target: "acct_2" },
      { source: "acct_2", target: "acct_3" },
    ],
  };

  return (
    <div className="bg-gray-800 p-4 rounded-xl shadow-lg text-white">
      <h2 className="text-xl font-semibold mb-3">Graph View</h2>
      {ForceGraph2D ? (
        <ForceGraph2D
          graphData={data}
          nodeLabel="id"
          nodeAutoColorBy="id"
          style={{ width: "100%", height: "400px" }}
        />
      ) : (
        <div className="text-gray-400">Loading graph...</div>
      )}
    </div>
  );
}
