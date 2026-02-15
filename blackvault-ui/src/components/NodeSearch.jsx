import { useState } from "react"
import { generateMockNode } from "../utils/mockGenerator"
import { getRiskColor } from "../utils/riskColors"

export default function NodeSearch() {
  const [nodeId, setNodeId] = useState("")
  const [node, setNode] = useState(null)

  const handleSearch = () => {
    setNode(generateMockNode(nodeId))
  }

  return (
    <div className="bg-gray-800 p-4 rounded-xl shadow-lg">
      <h2 className="text-xl font-semibold mb-3">Node Lookup</h2>
      <div className="flex gap-2 mb-3">
        <input
          type="text"
          placeholder="Enter Node ID"
          value={nodeId}
          onChange={(e) => setNodeId(e.target.value)}
          className="p-1 rounded text-black flex-1"
        />
        <button onClick={handleSearch} className="bg-blue-600 px-3 rounded">
          Search
        </button>
      </div>
      {node && (
        <div>
          <p>Risk: <span className={getRiskColor(node.risk)}>{node.risk}</span></p>
          <p>Hops to bad: {node.hops_to_bad}</p>
          <p>Recent transfers: {node.recent_count}</p>
          <p>Reasons: {node.reasons.join(", ")}</p>
        </div>
      )}
    </div>
  )
}
