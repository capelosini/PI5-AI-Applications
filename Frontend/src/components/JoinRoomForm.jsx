import { useState } from "react";

export default function JoinRoomForm({ activePlayer, match, onSubmit, onCancel }) {
  const hasTuring = match ? !!match.turingPlayer : false;
  const hasLovelace = match ? !!match.lovelacePlayer : false;

  const getInitialTeamSlot = () => {
    if (hasTuring && !hasLovelace) return 2;
    if (!hasTuring && hasLovelace) return 1;
    return 1;
  };

  const isLocked = match ? (hasTuring !== hasLovelace) : false;

  const [config, setConfig] = useState({
    player_id: activePlayer?.id || 0,
    team_slot: getInitialTeamSlot(),
  });

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    setConfig((prev) => ({
      ...prev,
      [name]: name === "team_slot" ? parseInt(value, 10) : (type === "number" ? parseInt(value) : value),
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(config);
  };

  return (
    <form className="config-form" onSubmit={handleSubmit}>
      <h2>Join Room</h2>

      <div className="form-group">
        <label>Joining as</label>
        <div
          style={{
            padding: "0.8rem",
            backgroundColor: "#25252d",
            borderRadius: "6px",
            color: "#ff4d4d",
            fontWeight: "bold",
            border: "1px solid #333",
          }}
        >
          {activePlayer?.aiPlayerName || "Anonymous"} (ID: {activePlayer?.id})
        </div>
      </div>

      <div className="form-group">
        <label htmlFor="team_slot">Team Slot</label>
        <select
          id="team_slot"
          name="team_slot"
          value={config.team_slot}
          onChange={handleChange}
          disabled={isLocked}
        >
          <option value={1} disabled={hasTuring}>
            Team 1 (Turing){hasTuring ? " - Taken" : ""}
          </option>
          <option value={2} disabled={hasLovelace}>
            Team 2 (Lovelace){hasLovelace ? " - Taken" : ""}
          </option>
        </select>
        {isLocked && (
          <span style={{ fontSize: "0.8rem", color: "#888", marginTop: "0.3rem", display: "block" }}>
            The other team is occupied. The empty slot has been locked in automatically.
          </span>
        )}
      </div>

      <div className="button-group" style={{ marginTop: "1.5rem" }}>
        <button type="submit" className="btn btn-primary">
          Join
        </button>
        <button type="button" className="btn btn-secondary" onClick={onCancel}>
          Cancel
        </button>
      </div>
    </form>
  );
}
