import styles from "../dashboard.module.css";
import { riskColor } from "../../lib/riskColor";
import { useState } from "react";

type Props = {
  account: any;
  onClose: () => void;
  onReviewAction: (
    accountId: string,
    action: "open" | "under_review" | "confirm_fraud" | "false_positive" | "escalate" | "snooze",
    payload?: { reviewer?: string; notes?: string; snooze_hours?: number }
  ) => Promise<void> | void;
};

function fmt(v: any) {
  if (typeof v === "number") return Number.isInteger(v) ? String(v) : v.toFixed(4);
  if (v === null || v === undefined) return "-";
  return String(v);
}

function KVTable({ title, obj }: { title: string; obj: Record<string, any> }) {
  const entries = Object.entries(obj || {});
  if (!entries.length) return null;

  return (
    <div className={styles.metricsBlock}>
      <div className={styles.metricsTitle}>{title}</div>
      <div className={styles.metricsGrid}>
        {entries.map(([k, v]) => (
          <div key={`${title}-${k}`} className={styles.metricRow}>
            <div className={styles.metricKey}>{k}</div>
            <div className={styles.metricVal}>{fmt(v)}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function AccountMetricsModal({ account, onClose, onReviewAction }: Props) {
  if (!account) return null;

  const metrics = account.metrics || {};
  const components = metrics.components || {};
  const recentTx = account.recent_transactions || [];
  const review = account.review || {};
  const [reviewer, setReviewer] = useState("analyst");
  const [notes, setNotes] = useState("");

  const scoreKeys = [
    "behavioral_score",
    "financial_score",
    "structural_score",
    "suspicion_score",
    "maturity_penalty_score",
    "raw_risk",
    "smoothed_risk",
    "final_risk",
  ];

  const orderedScores: Record<string, any> = {};
  for (const key of scoreKeys) orderedScores[key] = components[key];

  const currentRisk = Number(components.final_risk ?? account.risk ?? 0);

  return (
    <div className={styles.modalOverlay} onClick={onClose}>
      <div className={styles.modalCard} onClick={(e) => e.stopPropagation()}>
        <div className={styles.modalHeader}>
          <div>
            <div className={styles.sectionTitle}>BlackVault Account Investigation</div>
            <div className={styles.modalSub}>Account: {account.id}</div>
          </div>
          <button className={styles.button} onClick={onClose}>Close</button>
        </div>

        <div className={styles.modalDetailsGrid}>
          <div className={styles.kpiMini}>
            <div className={styles.kpiLabel}>Current Risk</div>
            <div className={styles.kpiValue} style={{ color: riskColor(currentRisk) }}>{currentRisk.toFixed(2)}</div>
          </div>
          <div className={styles.kpiMini}>
            <div className={styles.kpiLabel}>Hops To Bad</div>
            <div className={styles.kpiValue}>{fmt(account.hops_to_bad)}</div>
          </div>
          <div className={styles.kpiMini}>
            <div className={styles.kpiLabel}>Out Neighbors</div>
            <div className={styles.kpiValue}>{fmt(account.out_neighbors_count)}</div>
          </div>
          <div className={styles.kpiMini}>
            <div className={styles.kpiLabel}>Alert</div>
            <div className={styles.kpiValue}>{account.alert_set ? "SET" : "NOT SET"}</div>
          </div>
        </div>

        <div className={styles.metricsBlock}>
          <div className={styles.metricsTitle}>Review Workflow</div>
          <div style={{ display: "grid", gap: 8 }}>
            <div style={{ fontSize: 13, opacity: 0.8 }}>
              Status: <b>{review.status || "NONE"}</b>
              {review.reviewer ? ` | reviewer: ${review.reviewer}` : ""}
            </div>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              <input
                value={reviewer}
                onChange={(e) => setReviewer(e.target.value)}
                placeholder="reviewer"
                style={{ padding: "8px 10px", borderRadius: 8, border: "1px solid rgba(255,255,255,0.2)", background: "rgba(255,255,255,0.06)", color: "inherit" }}
              />
              <input
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="notes"
                style={{ padding: "8px 10px", borderRadius: 8, border: "1px solid rgba(255,255,255,0.2)", background: "rgba(255,255,255,0.06)", color: "inherit", minWidth: 220 }}
              />
            </div>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              <button className={styles.button} onClick={() => onReviewAction(account.id, "open", { reviewer, notes })}>Open</button>
              <button className={styles.buttonGhost} onClick={() => onReviewAction(account.id, "under_review", { reviewer, notes })}>Under Review</button>
              <button className={styles.button} onClick={() => onReviewAction(account.id, "confirm_fraud", { reviewer, notes })}>Confirm Fraud</button>
              <button className={styles.buttonGhost} onClick={() => onReviewAction(account.id, "false_positive", { reviewer, notes })}>False Positive</button>
              <button className={styles.button} onClick={() => onReviewAction(account.id, "escalate", { reviewer, notes })}>Escalate</button>
              <button className={styles.buttonGhost} onClick={() => onReviewAction(account.id, "snooze", { reviewer, notes, snooze_hours: 24 })}>Snooze 24h</button>
            </div>
          </div>
        </div>

        <KVTable title="Risk Engine Scores" obj={orderedScores} />

        <div className={styles.metricsBlock}>
          <div className={styles.metricsTitle}>AI Overview</div>
          <p>{account.aiSummary || "No AI summary yet."}</p>
        </div>

        <div className={styles.metricsBlock}>
          <div className={styles.metricsTitle}>Recent 10 Transactions</div>
          <div className={styles.scrollContainer} style={{ maxHeight: 260 }}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Sender</th>
                  <th>Receiver</th>
                  <th>Amount</th>
                  <th>Risk</th>
                </tr>
              </thead>
              <tbody>
                {recentTx.map((tx: any, idx: number) => (
                  <tr key={`${tx.id || idx}-${idx}`}>
                    <td>{tx.sender}</td>
                    <td>{tx.receiver}</td>
                    <td>${Number(tx.amount || 0).toFixed(2)}</td>
                    <td style={{ color: riskColor(Number(tx.risk || 0)), fontWeight: 700 }}>
                      {Number(tx.risk || 0).toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {recentTx.length === 0 && <p style={{ opacity: 0.7 }}>No recent transactions found for this account.</p>}
        </div>
      </div>
    </div>
  );
}
