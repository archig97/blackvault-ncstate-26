export function riskColor(risk: number) {
  if (risk >= 80) return "#ef4444";
  if (risk >= 60) return "#f97316";
  if (risk >= 40) return "#facc15";
  return "#22c55e";
}
