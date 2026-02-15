// Text color for risk values
export function getRiskColor(risk) {
  if (risk > 80) return "text-red-500";
  if (risk > 50) return "text-yellow-400";
  return "text-green-400";
}

// Background color for risk badges
export function getRiskBgColor(risk) {
  if (risk > 80) return "bg-red-500/20 text-red-400 border border-red-500/50";
  if (risk > 50) return "bg-yellow-500/20 text-yellow-400 border border-yellow-500/50";
  return "bg-green-500/20 text-green-400 border border-green-500/50";
}

// Risk badge label
export function getRiskBadge(risk) {
  if (risk > 80) return "HIGH";
  if (risk > 50) return "MEDIUM";
  return "LOW";
}
