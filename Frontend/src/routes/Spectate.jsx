import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router";
import { API } from "@/utils/API";
import GameBoard from "@/components/GameBoard";

export default function Spectate() {
  const { gameId } = useParams();
  const navigate = useNavigate();
  const [match, setMatch] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchGameStatus = useCallback(async () => {
    try {
      const data = await API.games.get(gameId);
      setMatch(data);
      setError(null);
    } catch (err) {
      console.error("Failed to fetch game status:", err);
      setError("Failed to load game state. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [gameId]);

  useEffect(() => {
    fetchGameStatus();
  }, [fetchGameStatus]);

  if (loading && !match) {
    return (
      <div className="home-container">
        <p>Loading game state...</p>
      </div>
    );
  }

  const getTurnTeamName = () => {
    if (!match) return "N/A";
    return match.currentTurnTeamId === 1 ? "Turing" : "Lovelace";
  };

  return (
    <div className="home-container" style={{ maxWidth: "800px" }}>
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "2rem",
        }}
      >
        <h1 style={{ margin: 0, fontSize: "1.5rem" }}>Spectating Game</h1>
        <div style={{ display: "flex", gap: "1rem" }}>
          <button
            className="btn btn-secondary btn-sm"
            onClick={fetchGameStatus}
          >
            Refresh
          </button>
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => navigate("/")}
          >
            Back to Lobby
          </button>
        </div>
      </header>

      {error && (
        <p style={{ color: "#ff4d4d", marginBottom: "1rem" }}>{error}</p>
      )}

      {match && (
        <>
          <div className="game-info-panel">
            <div className="info-item">
              <span className="info-label">Status</span>
              <span
                className={`match-status status-${match.status.toLowerCase()}`}
              >
                {match.formattedStatus}
              </span>
            </div>
            <div className="info-item">
              <span className="info-label">Turn</span>
              <span className="info-value">
                #{match.currentTurnNumber} -{" "}
                <span className="turn-active">{getTurnTeamName()}</span>
              </span>
            </div>
            <div className="info-item">
              <span className="info-label">Phase</span>
              <span
                className="info-value"
                style={{ textTransform: "capitalize" }}
              >
                {match.currentTurnPhase?.replace("_", " ") || "N/A"}
              </span>
            </div>
          </div>

          <div
            className="board-container"
            style={{
              padding: "2rem",
              backgroundColor: "#25252d",
              borderRadius: "12px",
              border: "1px solid #333",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: "2rem",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                width: "100%",
                fontSize: "0.9rem",
              }}
            >
              <div style={{ textAlign: "left" }}>
                <span className="team-label">Turing Team</span>
                <div className="player-name" style={{ fontSize: "1.1rem" }}>
                  {match.turingName}
                </div>
              </div>
              <div style={{ textAlign: "right" }}>
                <span className="team-label">Lovelace Team</span>
                <div className="player-name" style={{ fontSize: "1.1rem" }}>
                  {match.lovelaceName}
                </div>
              </div>
            </div>

            <GameBoard board={match.board} />

            <code
              style={{
                fontSize: "0.7rem",
                color: "#666",
                wordBreak: "break-all",
              }}
            >
              ID: {match.id}
            </code>
          </div>
        </>
      )}
    </div>
  );
}
