import { getRiskColor } from "../utils/riskColors"

export default function Leaderboard({ leaderboard }) {
  return (
    <div className="bg-gray-800 p-4 rounded-xl shadow-lg">
      <h2 className="text-xl font-semibold mb-3">Top Risky Accounts</h2>
      <ol className="list-decimal pl-5">
        {leaderboard.map((item, idx) => (
          <li key={item.node} className={getRiskColor(item.risk)}>
            {item.node} — {item.risk}
          </li>
        ))}
      </ol>
    </div>
  )
}
