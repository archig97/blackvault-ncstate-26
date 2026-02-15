import { useMemo, useState } from "react";
import styles from "../dashboard.module.css";
import { riskColor } from "../../lib/riskColor";

export default function TransactionFeed({ transactions }: any) {
  const [order, setOrder] = useState<"desc" | "asc">("desc");
  const [riskFilter, setRiskFilter] = useState<"all" | "40" | "70">("all");

  const rows = useMemo(() => {
    const minRisk = riskFilter === "all" ? -1 : Number(riskFilter);
    return [...(transactions || [])]
      .filter((tx: any) => Number(tx.risk || 0) >= minRisk)
      .sort((a: any, b: any) => {
        const ra = Number(a.risk || 0);
        const rb = Number(b.risk || 0);
        return order === "desc" ? rb - ra : ra - rb;
      });
  }, [transactions, order, riskFilter]);

  return (
    <div className={styles.card}>
      <div className={styles.cardHeaderRow}>
        <div className={styles.sectionTitle}>Live Transactions</div>
        <div className={styles.filterRow}>
          <label className={styles.filterLabel}>Risk Filter</label>
          <select
            className={styles.select}
            value={riskFilter}
            onChange={(e) => setRiskFilter(e.target.value as any)}
          >
            <option value="all">All</option>
            <option value="40">40+</option>
            <option value="70">70+ (Suspicious)</option>
          </select>
          <label className={styles.filterLabel}>Sort</label>
          <select
            className={styles.select}
            value={order}
            onChange={(e) => setOrder(e.target.value as any)}
          >
            <option value="desc">DESC</option>
            <option value="asc">ASC</option>
          </select>
        </div>
      </div>

      <div className={styles.scrollContainer}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Sender</th>
              <th>Receiver</th>
              <th>Amount</th>
              <th title="Risk score 0-100 computed by BlackVault risk engine">Risk</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((tx: any, i: number) => (
              <tr key={`${tx.id || i}-${tx.ts || i}`}>
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
    </div>
  );
}
