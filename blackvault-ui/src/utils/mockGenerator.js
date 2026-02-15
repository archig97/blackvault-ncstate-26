export function generateMockTx(attackMode = false) {
  let risk = Math.floor(Math.random() * 100)
  if (attackMode) {
    risk = 85 + Math.floor(Math.random() * 15)
  }

  return {
    id: Date.now(),
    sender: "acct_" + Math.floor(Math.random() * 10),
    receiver: "acct_" + Math.floor(Math.random() * 10),
    amount: (Math.random() * 5000).toFixed(2),
    risk,
    flagged: risk > 70,
    reasons: risk > 70 ? ["Burst transfers", "2 hops from scam wallet"] : []
  }
}

export function generateMockNode(id) {
  return {
    id,
    risk: Math.floor(Math.random() * 100),
    hops_to_bad: Math.floor(Math.random() * 3),
    recent_count: Math.floor(Math.random() * 15),
    reasons: ["High fan-out", "Volume spike"]
  }
}

export function generateMockGraph() {
  return {
    nodes: Array.from({ length: 5 }, (_, i) => ({
      id: "acct_" + i,
      risk: Math.floor(Math.random() * 100)
    })),
    edges: [
      { from: "acct_0", to: "acct_1" },
      { from: "acct_0", to: "acct_2" },
      { from: "acct_2", to: "acct_3" }
    ]
  }
}
