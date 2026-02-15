"use client";

import dynamic from "next/dynamic";
import styles from "../dashboard.module.css";

const GraphComponent = dynamic(
  () => import("../../GraphNeighborhood"),
  { ssr: false }
);

export default function GraphWrapper({ data }: any) {
  return (
    <div className={styles.card}>
      <div className={styles.sectionTitle}>Network View</div>
      <GraphComponent graphData={data} />
    </div>
  );
}
