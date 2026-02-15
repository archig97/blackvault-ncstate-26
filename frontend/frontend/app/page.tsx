import dynamic from "next/dynamic";

const GraphNeighborhood = dynamic(() => import("./GraphNeighborhood"), {
  ssr: false,
});

export default function Home() {
  return (
    <main style={{ height: "100vh" }}>
      <GraphNeighborhood />
    </main>
  );
}
