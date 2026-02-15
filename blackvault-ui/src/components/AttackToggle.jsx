export default function AttackToggle({ attackMode, setAttackMode }) {
  return (
    <button
      onClick={() => setAttackMode(!attackMode)}
      className={`px-4 py-2 rounded ${
        attackMode ? "bg-red-600" : "bg-green-600"
      }`}
    >
      {attackMode ? "Stop Attack" : "Run Attack"}
    </button>
  )
}
