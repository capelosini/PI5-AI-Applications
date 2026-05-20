import Spectator from "@/utils/Spectator";

export default function SpectatorList({ spectators }) {
  if (!spectators || spectators.length === 0) {
    return (
      <div className="spectators-section">
        <h3 className="section-title">Spectators (0)</h3>
        <p style={{ color: "#666", fontSize: "0.9rem" }}>No spectators yet.</p>
      </div>
    );
  }

  return (
    <div className="spectators-section">
      <h3 className="section-title">Spectators ({spectators.length})</h3>
      <div className="spectator-grid">
        {spectators.map((s) => (
          <div key={s.id} className="spectator-badge" title={s.name}>
            <img src={s.avatar} alt={s.name} className="spectator-avatar" />
            <span className="spectator-name">{s.name}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
