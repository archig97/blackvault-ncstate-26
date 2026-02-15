"use client";

import { useEffect, useState } from "react";
import styles from "./dashboard.module.css";
import TransactionFeed from "./components/TransactionFeed";
import Leaderboard from "./components/Leaderboard";
import ThreatSummary from "./components/ThreatSummary";
import AccountMetricsModal from "./components/AccountMetricsModal";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
const isLegacyTxSummary = (text: string) =>
  Boolean(text && text.includes("->") && text.includes("| risk"));

export default function DashboardPage() {
  const [transactions, setTransactions] = useState<any[]>([]);
  const [totalTxCount, setTotalTxCount] = useState(0);
  const [topAccounts, setTopAccounts] = useState<any[]>([]);
  const [selectedAccount, setSelectedAccount] = useState<any>(null);
  const [threatSummary, setThreatSummary] = useState("Waiting for telemetry...");
  const [connected, setConnected] = useState(false);
  const [accountSearch, setAccountSearch] = useState("acct_attack");
  const [searchErr, setSearchErr] = useState("");

  useEffect(() => {
    const bootstrap = async () => {
      try {
        const res = await fetch(`${API_BASE}/dashboard/bootstrap`);
        if (!res.ok) return;
        const data = await res.json();
        setTransactions(data.transactions || []);
        setTotalTxCount(
          typeof data.tx_total === "number"
            ? data.tx_total
            : (data.transactions || []).length
        );
        setTopAccounts(data.top_accounts || []);
        const initialSummary = data.threat_summary || "Waiting for telemetry...";
        setThreatSummary(initialSummary);

        if (
          (initialSummary === "Waiting for telemetry..." || isLegacyTxSummary(initialSummary)) &&
          (typeof data.tx_total === "number" ? data.tx_total : 0) > 0
        ) {
          const refreshRes = await fetch(`${API_BASE}/ai/refresh-summary`, { method: "POST" });
          if (refreshRes.ok) {
            const refreshData = await refreshRes.json();
            if (refreshData.summary) setThreatSummary(refreshData.summary);
          }
        }
      } catch {
        // websocket flow continues even if bootstrap fails
      }
    };

    bootstrap();

    const wsUrl = API_BASE.replace("http://", "ws://").replace("https://", "wss://");
    const ws = new WebSocket(`${wsUrl}/ws`);

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "bootstrap") {
        setTransactions(data.transactions || []);
        setTotalTxCount(
          typeof data.tx_total === "number"
            ? data.tx_total
            : (data.transactions || []).length
        );
        setTopAccounts(data.top_accounts || []);
        setThreatSummary(data.threat_summary || "Waiting for telemetry...");
      }

      if (data.type === "new_tx") {
        setTransactions((prev) => [data.transaction, ...prev.slice(0, 120)]);
        setTotalTxCount((prev) => prev + 1);

        if (data.account_update) {
          setTopAccounts((prev) => {
            const filtered = prev.filter((a) => a.id !== data.account_update.id);
            return [data.account_update, ...filtered]
              .sort((a, b) => Number(b.risk || 0) - Number(a.risk || 0))
              .slice(0, 20);
          });
        }
      }

      if (data.type === "threat_summary") {
        setThreatSummary(data.summary);
      }
    };
    return () => ws.close();
  }, []);

  const onSelectAccount = async (account: any) => {
    setSelectedAccount(account);
    try {
      const res = await fetch(`${API_BASE}/account/${encodeURIComponent(account.id)}`);
      if (!res.ok) return;
      const details = await res.json();
      setSelectedAccount(details);
    } catch {
      // keep quick local view if API detail fails
    }
  };

  const onSearchAccount = async () => {
    setSearchErr("");
    const value = accountSearch.trim();
    if (!value) {
      setSearchErr("Enter an account id");
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/account/${encodeURIComponent(value)}`);
      if (!res.ok) {
        setSearchErr(`Lookup failed (${res.status})`);
        return;
      }
      const details = await res.json();
      setSelectedAccount(details);
    } catch {
      setSearchErr("Could not fetch account details");
    }
  };

  const onSetAlert = async (accountId: string, enabled: boolean) => {
    try {
      let res = await fetch(`${API_BASE}/account/${encodeURIComponent(accountId)}/alert`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled }),
      });
      if (res.status === 404) {
        res = await fetch(`${API_BASE}/account/alert/${encodeURIComponent(accountId)}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ enabled }),
        });
      }
      if (!res.ok) return;
      const out = await res.json();
      const alertSet = Boolean(out?.alert_set);
      setTopAccounts((prev) =>
        prev.map((a) => (a.id === accountId ? { ...a, alert_set: alertSet } : a))
      );
      setSelectedAccount((prev: any) =>
        prev && prev.id === accountId ? { ...prev, alert_set: alertSet } : prev
      );
    } catch {
      // ignore transient failure; user can retry
    }
  };

  const highRiskCount = topAccounts.filter((a) => Number(a.risk || 0) >= 70).length;
  const avgRisk =
    transactions.length > 0
      ? (
          transactions.reduce((acc, t) => acc + Number(t.risk || 0), 0) /
          transactions.length
        ).toFixed(1)
      : "0";

  return (
    <div className={styles.wrapper}>
      <div className={styles.topBar}>
        <div>
          <div className={styles.brand}>BlackVault</div>
          <div className={styles.title}>Fraud Intelligence Dashboard</div>
          <div className={styles.bankName}>Bank: BlackVault National Bank</div>
        </div>

        <div className={styles.rightControls}>
          <span
            className={`${styles.statusBadge} ${connected ? styles.live : styles.offline}`}
          >
            {connected ? "Live Connected" : "Disconnected"}
          </span>

          <button className={styles.button} onClick={() => window.open("/", "_blank")}>Open Network View</button>
          <button className={styles.buttonGhost} onClick={() => window.location.reload()}>Refresh</button>
        </div>
      </div>

      <div className={styles.searchBar}>
        <input
          className={styles.searchInput}
          value={accountSearch}
          onChange={(e) => setAccountSearch(e.target.value)}
          placeholder="Search account id (e.g., acct_44)"
        />
        <button className={styles.button} onClick={onSearchAccount}>Search Account</button>
        {searchErr ? <span className={styles.errorText}>{searchErr}</span> : null}
      </div>

      <div className={styles.kpiGrid}>
        <div className={styles.kpiCard}>
          <div className={styles.kpiLabel}>Total Transactions</div>
          <div className={styles.kpiValue}>{totalTxCount}</div>
        </div>

        <div className={styles.kpiCard}>
          <div className={styles.kpiLabel}>High Risk Accounts</div>
          <div className={styles.kpiValue}>{highRiskCount}</div>
        </div>

        <div className={styles.kpiCard}>
          <div className={styles.kpiLabel}>Average Risk</div>
          <div className={styles.kpiValue}>{avgRisk}</div>
        </div>

        <div className={styles.kpiCard}>
          <div className={styles.kpiLabel}>Active Alerts</div>
          <div className={styles.kpiValue}>{highRiskCount}</div>
        </div>
      </div>

      <ThreatSummary summary={threatSummary} />

      <div className={styles.mainGrid}>
        <TransactionFeed transactions={transactions} />
        <Leaderboard accounts={topAccounts} onSelect={onSelectAccount} onSetAlert={onSetAlert} />
      </div>

      {selectedAccount && (
        <AccountMetricsModal
          account={selectedAccount}
          onClose={() => setSelectedAccount(null)}
        />
      )}
    </div>
  );
}
