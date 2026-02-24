import { useMemo, useState } from "react";
import styles from "../dashboard.module.css";
import { riskColor } from "../../lib/riskColor";

function getImportantScore(acc: any) {
  const comps = acc?.metrics?.components || {};
  const v = comps.final_risk ?? acc?.risk ?? 0;
  return Number(v || 0);
}

export default function Leaderboard({ accounts, onSelect, onSetAlert }: any) {
  const [order, setOrder] = useState<"desc" | "asc">("desc");
  const [riskFilter, setRiskFilter] = useState<"all" | "40" | "70">("70");

  const rows = useMemo(() => {
    const minRisk = riskFilter === "all" ? -1 : Number(riskFilter);
    return [...(accounts || [])]
      .filter((a: any) => Number(a.risk || 0) >= minRisk)
      .sort((a: any, b: any) => {
        const sa = getImportantScore(a);
        const sb = getImportantScore(b);
        return order === "desc" ? sb - sa : sa - sb;
      });
  }, [accounts, order, riskFilter]);

  return (
    <div className={styles.card}>
      <div className={styles.cardHeaderRow}>
        <div className={styles.sectionTitle}>Top Risk Accounts</div>
        <div className={styles.filterRow}>
          <label className={styles.filterLabel}>Risk Filter</label>
          <select
            className={styles.select}
            value={riskFilter}
            onChange={(e) => setRiskFilter(e.target.value as any)}
          >
            <option value="all">All</option>
            <option value="40">40+</option>
            <option value="70">70+</option>
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

      {rows.length === 0 && <p style={{ opacity: 0.7 }}>No matching accounts.</p>}

      <div className={styles.accountList}>
        {rows.map((acc: any) => {
          const imp = getImportantScore(acc);
          const structural = Number(acc?.metrics?.components?.structural_score || 0);
          const canAlert = Number(acc?.risk || 0) >= 70;
          return (
            <div key={acc.id} className={styles.accountItemRow}>
              <button
                className={styles.accountItemButton}
                onClick={() => onSelect(acc)}
              >
                <div>
                  <div className={styles.accountId}>{acc.id}</div>
                  <div className={styles.accountMeta}>
                    hops: {acc.hops_to_bad ?? "-"} | review: {acc?.review?.status || "NONE"}
                  </div>
                </div>

                <div className={styles.scoreCluster}>
                  <div
                    className={styles.scoreBadge}
                    title="Primary score shown: final_risk from risk engine components"
                    style={{ color: riskColor(imp) }}
                  >
                    {imp.toFixed(2)}
                  </div>
                  <div
                    className={styles.miniScore}
                    title="Structural score indicates graph/network risk contribution"
                  >
                    structural: {structural.toFixed(2)}
                  </div>
                </div>
              </button>

              {!acc.alert_set ? (
                <button
                  className={styles.alertButton}
                  disabled={!canAlert}
                  onClick={() => onSetAlert(acc.id, true)}
                  title={!canAlert ? "Alert can be set only for high-risk accounts (70+)" : "Set persistent alert flag for this account"}
                >
                  Set Alert
                </button>
              ) : (
                <button
                  className={styles.alertButtonSet}
                  onClick={() => onSetAlert(acc.id, false)}
                  title="Unset alert flag for this account"
                >
                  Unset Alert
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
