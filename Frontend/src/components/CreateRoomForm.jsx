import { useState } from "react";

export default function CreateRoomForm({ activePlayer, onSubmit, onCancel }) {
  const [config, setConfig] = useState({
    auto_start: false,
    player_id: activePlayer?.id || 0,
    team_slot: 1,
    vs_random_bot: false,
  });

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setConfig((prev) => ({
      ...prev,
      [name]:
        type === "checkbox"
          ? checked
          : type === "number"
            ? parseInt(value)
            : value,
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(config);
  };

  return (
    <form className="config-form" onSubmit={handleSubmit}>
      <h2>Room Configuration</h2>

      <div className="form-group">
        <label>Creating as</label>
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

      <div className="form-checkbox-group">
        <label>
          <input
            type="checkbox"
            name="auto_start"
            checked={config.auto_start}
            onChange={handleChange}
          />
          Auto Start
        </label>
      </div>

      <div className="form-checkbox-group">
        <label>
          <input
            type="checkbox"
            name="vs_random_bot"
            checked={config.vs_random_bot}
            onChange={handleChange}
          />
          Vs Random Bot
        </label>
      </div>

      <div className="button-group" style={{ marginTop: "1.5rem" }}>
        <button type="submit" className="btn btn-primary">
          Create
        </button>
        <button type="button" className="btn btn-secondary" onClick={onCancel}>
          Cancel
        </button>
      </div>
    </form>
  );
}
