import styles from "../dashboard.module.css";

export default function ThreatSummary({ summary }: any) {
  return (
    <div className={styles.card}>
      <div className={styles.sectionTitle}>AI Threat Overview</div>
      <p style={{ lineHeight: "1.6", opacity: 0.9 }}>
        {summary}
      </p>
    </div>
  );
}
