import { useState } from "react";

export default function JoinRoomForm({ activePlayer, onSubmit, onCancel }) {
  const [config, setConfig] = useState({
    player_id: activePlayer?.id || 0,
    team_slot: 1,
  });

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    setConfig((prev) => ({
      ...prev,
      [name]: type === "number" ? parseInt(value) : value,
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
        >
          <option value={1}>Team 1 (Turing)</option>
          <option value={2}>Team 2 (Lovelace)</option>
        </select>
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
