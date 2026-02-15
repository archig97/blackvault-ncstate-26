import styles from "../dashboard.module.css";
import { riskColor } from "../../lib/riskColor";

export default function AccountDetails({ account }: any) {
  if (!account) return null;

  return (
    <div className={styles.card}>
      <div className={styles.sectionTitle}>Account Details</div>

      <p><strong>ID:</strong> {account.id}</p>
      <p>
        <strong>Risk:</strong>{" "}
        <span style={{ color: riskColor(account.risk) }}>
          {account.risk}
        </span>
      </p>

      <h4 style={{ marginTop: 15 }}>Reasons</h4>
      <ul>
        {account.reasons?.map((r: string, i: number) => (
          <li key={i}>{r}</li>
        ))}
      </ul>

      <h4 style={{ marginTop: 15 }}>AI Explanation</h4>
      <p>{account.aiSummary}</p>
    </div>
  );
}
