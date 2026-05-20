import { useState, useEffect, useCallback, useRef } from "react";
import { useParams, useNavigate } from "react-router";
import { API, setAuthToken, getWebSocketUrl } from "@/utils/API";
import GameBoard from "@/components/GameBoard";
import SpectatorList from "@/components/SpectatorList";
import AccountManager from "@/utils/AccountManager";
import SpectatorManager from "@/utils/SpectatorManager";
import Match from "@/utils/Match";
import Spectator from "@/utils/Spectator";

export default function Spectate() {
  const { gameId } = useParams();
  const navigate = useNavigate();
  const [match, setMatch] = useState(null);
  const [spectators, setSpectators] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [spectatorToken, setSpectatorToken] = useState(
    SpectatorManager.getSession(gameId),
  );
  const [isLive, setIsLive] = useState(false);
  const wsRef = useRef(null);

  const registerAsSpectator = useCallback(async () => {
    try {
      const existingToken = SpectatorManager.getSession(gameId);
      if (existingToken) {
        console.log("Reusing existing spectator token");
        setSpectatorToken(existingToken);
        return existingToken;
      }

      const active = AccountManager.getActivePlayer();
      const name =
        active?.aiPlayerName ||
        `Spectator_${Math.random().toString(36).substring(7)}`;
      const avatar =
        active?.aiPlayerAvatar ||
        `https://api.dicebear.com/7.x/bottts/svg?seed=${name}`;

      const spectatorData = await API.games.addSpectator(gameId, {
        spectator_name: name,
        spectator_avatar: avatar,
      });

      SpectatorManager.saveSession(gameId, spectatorData.accessToken);
      setSpectatorToken(spectatorData.accessToken);
      return spectatorData.accessToken;
    } catch (err) {
      console.error("Failed to register as spectator:", err);
      // If it failed because of an invalid token, we might want to clear it
      if (err.message.includes("401") || err.message.includes("403")) {
        SpectatorManager.removeSession(gameId);
      }
      setError("Failed to register as spectator. " + err.message);
      return null;
    }
  }, [gameId]);

  const connectWebSocket = useCallback(
    (token) => {
      if (wsRef.current) {
        wsRef.current.close();
      }

      const url = getWebSocketUrl(`/ws/games/${gameId}?token=${token}`);
      console.log("Connecting to WebSocket:", url);
      const ws = new WebSocket(url);

      ws.onopen = () => {
        console.log("WebSocket connected");
        setIsLive(true);
        setError(null);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log("WebSocket message received:", data);

          if (data.game_id || data.id) {
            setMatch((prevMatch) => {
              if (!prevMatch) return new Match(data);

              // If the status changes, we should disconnect and fetch the full state
              if (data.status && data.status !== prevMatch.status) {
                console.log(
                  `Status changed from ${prevMatch.status} to ${data.status}, refreshing...`,
                );

                setTimeout(() => {
                  if (wsRef.current) wsRef.current.close();
                  fetchGameStatus().then((updatedMatch) => {
                    if (updatedMatch && updatedMatch.status !== "FINISHED") {
                      const token = SpectatorManager.getSession(gameId);
                      if (token) connectWebSocket(token);
                    }
                  });
                }, 0);

                return prevMatch;
              }

              // Handle full object if provided (old format or full update)
              if (data.id) {
                const updated = new Match(data);
                setSpectators(updated.spectators);
                return updated;
              }

              // Partial update from new WS format
              return prevMatch.updateFromWS(data);
            });
          }
        } catch (err) {
          console.error("Error parsing WebSocket message:", err);
        }
      };

      ws.onclose = (event) => {
        console.log("WebSocket disconnected", event.reason);
        setIsLive(false);
        // Reconnect logic could go here if needed
      };

      ws.onerror = (err) => {
        console.error("WebSocket error:", err);
        setIsLive(false);
        setError("Real-time connection lost. Updates may be delayed.");
      };

      wsRef.current = ws;
    },
    [gameId],
  );

  const fetchGameStatus = useCallback(async () => {
    try {
      const data = await API.games.get(gameId);
      setMatch(data);
      setSpectators(data.spectators);
      setError(null);
      return data;
    } catch (err) {
      console.error("Failed to fetch game status:", err);
      setError("Failed to load game state. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [gameId]);

  useEffect(() => {
    const active = AccountManager.getActivePlayer();
    if (active?.accessToken) {
      setAuthToken(active.accessToken);
    }

    const initSpectating = async () => {
      setLoading(true);
      // First fetch current status
      const currentMatch = await fetchGameStatus();

      // Then register as spectator to get WS token
      // Don't connect if match is already finished
      if (currentMatch && currentMatch.status !== "FINISHED") {
        const token = await registerAsSpectator();
        if (token) {
          connectWebSocket(token);
        }
      }
      setLoading(false);
    };

    initSpectating();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [fetchGameStatus, registerAsSpectator, connectWebSocket]);

  // Periodic update for spectators and to ensure sync
  useEffect(() => {
    if (!gameId || (match && match.status === "FINISHED")) return;

    const interval = setInterval(() => {
      console.log("Periodic sync/spectator list update");
      fetchGameStatus();
    }, 5000); // Every 30 seconds

    return () => clearInterval(interval);
  }, [gameId, match?.status, fetchGameStatus]);

  if (loading && !match) {
    return (
      <div className="home-container">
        <p>Initializing spectate mode...</p>
      </div>
    );
  }

  const handleStartMatch = async () => {
    try {
      setLoading(true);
      await API.games.start(gameId);
      // WS will likely update the state, but we can fetch just in case
      await fetchGameStatus();
    } catch (err) {
      console.error("Failed to start match:", err);
      setError("Failed to start match: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const activePlayer = AccountManager.getActivePlayer();
  const canStart =
    match &&
    match.status === "PAUSED" &&
    activePlayer &&
    String(match.createdBy) === String(activePlayer.id) &&
    match.turingPlayer &&
    match.lovelacePlayer;

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
          {canStart && (
            <button
              className="btn btn-primary btn-sm"
              onClick={handleStartMatch}
              disabled={loading}
            >
              {loading ? "Starting..." : "Start Match"}
            </button>
          )}
          <button
            className="btn btn-secondary btn-sm"
            onClick={fetchGameStatus}
            disabled={loading}
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
        <div
          style={{
            padding: "0.8rem",
            backgroundColor: "rgba(255, 77, 77, 0.1)",
            border: "1px solid #ff4d4d",
            borderRadius: "8px",
            color: "#ff4d4d",
            marginBottom: "1.5rem",
            fontSize: "0.9rem",
          }}
        >
          {error}
        </div>
      )}

      {match && (
        <>
          {match.status === "FINISHED" && (
            <div
              className="winner-announcement"
              style={{
                backgroundColor: "rgba(46, 125, 50, 0.1)",
                border: "1px solid #2e7d32",
                borderRadius: "12px",
                padding: "1.5rem",
                marginBottom: "2rem",
                textAlign: "center",
              }}
            >
              <h2
                style={{
                  color: "#2e7d32",
                  margin: "0 0 0.5rem 0",
                  fontSize: "1.8rem",
                }}
              >
                Match Finished!
              </h2>
              <p style={{ fontSize: "1.3rem", margin: 0 }}>
                Winner:{" "}
                <strong style={{ color: "#fdfdfd" }}>{match.winnerName}</strong>
              </p>
              <p style={{ color: "#888", marginTop: "0.5rem" }}>
                Team: {match.winnerTeam === 1 ? "Turing" : "Lovelace"}
              </p>
            </div>
          )}

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

            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                width: "100%",
                alignItems: "center",
              }}
            >
              <code
                style={{
                  fontSize: "0.7rem",
                  color: "#666",
                  wordBreak: "break-all",
                }}
              >
                ID: {match.id}
              </code>
              <div
                style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}
              >
                <div
                  style={{
                    width: "8px",
                    height: "8px",
                    backgroundColor: isLive ? "#2e7d32" : "#ff4d4d",
                    borderRadius: "50%",
                  }}
                ></div>
                <span style={{ fontSize: "0.7rem", color: "#666" }}>
                  {isLive ? "Live" : "Disconnected"}
                </span>
              </div>
            </div>
          </div>

          <SpectatorList spectators={spectators} />
        </>
      )}
    </div>
  );
}
