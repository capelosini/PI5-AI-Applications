import { useState, useEffect, useCallback } from "react";
import CreateRoomForm from "@/components/CreateRoomForm";
import JoinRoomForm from "@/components/JoinRoomForm";
import AccountManagement from "@/components/AccountManagement";
import PlayerList from "@/components/PlayerList";
import MatchList from "@/components/MatchList";
import Match from "@/utils/Match";
import AccountManager from "@/utils/AccountManager";
import { API, setAuthToken } from "@/utils/API";

export default function Home() {
    const [view, setView] = useState("lobby"); // "lobby", "create", "join", "accounts", "players"
    const [matches, setMatches] = useState([]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeAccount, setActiveAccount] = useState(
    AccountManager.getActivePlayer(),
  );

  const fetchMatches = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await API.games.list({ page_size: 50 });
      setMatches(Match.fromArray(response.items));
    } catch (err) {
      console.error("Failed to fetch matches:", err);
      setError("Failed to load matches. Authentication may be required.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
      const active = AccountManager.getActivePlayer();
      if (active?.accessToken) {
          setAuthToken(active.accessToken);
      }

      if (view === "lobby") {
          fetchMatches();
      }
  }, [view, fetchMatches]);

  const handleAccountChange = () => {
      const active = AccountManager.getActivePlayer();
      setActiveAccount(active);
      if (active?.accessToken) {
          setAuthToken(active.accessToken);
      }
      setView("lobby");
      fetchMatches();
  };
  const handleCreateRoom = async (config) => {
    try {
      await API.games.create(config);
      setView("lobby");
      fetchMatches();
    } catch (err) {
      alert("Error creating room: " + err.message);
    }
  };

  const handleJoinRoom = async (config) => {
    // Note: Joining usually requires a gameId.
    // This is a simplified placeholder; real join logic would need the ID from state or selection.
    console.log("Joining room with config:", config);
    setView("lobby");
    fetchMatches();
  };

  const handleQuickJoin = (matchId) => {
    console.log("Quick joining match:", matchId);
    setView("join");
  };

  return (
    <div className="home-container">
      {view === "lobby" && (
        <>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "1rem",
            }}
          >
            <h1 style={{ margin: 0 }}>Game Lobby</h1>
            <div
              className="active-user-badge"
              onClick={() => setView("accounts")}
            >
              {activeAccount?.aiPlayerAvatar && (
                <img 
                  src={activeAccount.aiPlayerAvatar} 
                  alt="" 
                  className="badge-avatar"
                />
              )}
              {activeAccount
                ? activeAccount.aiPlayerName || activeAccount.groupName
                : "No Account"}
            </div>
          </div>

          <div
            style={{
              display: "flex",
              justifyContent: "flex-end",
              marginBottom: "1rem",
            }}
          >
            <button
              className={`btn btn-secondary btn-sm ${loading ? "loading" : ""}`}
              onClick={fetchMatches}
              disabled={loading}
            >
              {loading ? "Refreshing..." : "Refresh"}
            </button>
          </div>

          <div className="button-group">
              <button className="btn btn-primary" onClick={() => setView("create")}>
                  Create Room
              </button>
              <button className="btn btn-secondary" onClick={() => setView("join")}>
                  Join Room
              </button>
          </div>

          <div style={{ marginTop: '1rem' }}>
              <button 
                  className="btn btn-secondary" 
                  style={{ width: '100%' }}
                  onClick={() => setView("players")}
              >
                  Show Online Players
              </button>
          </div>


          {error && (
            <p style={{ color: "#ff4d4d", marginTop: "1rem" }}>{error}</p>
          )}

          <MatchList matches={matches} onJoin={handleQuickJoin} />
        </>
      )}

      {view === "accounts" && (
          <AccountManagement 
              onAccountChange={handleAccountChange}
              onCancel={() => setView("lobby")}
          />
      )}

      {view === "players" && (
          <PlayerList 
              onCancel={() => setView("lobby")}
          />
      )}
      {view === "create" && (
          <CreateRoomForm 
              activePlayer={activeAccount}
              onSubmit={handleCreateRoom} 
              onCancel={() => setView("lobby")} 
          />
      )}

      {view === "join" && (
          <JoinRoomForm 
              activePlayer={activeAccount}
              onSubmit={handleJoinRoom} 
              onCancel={() => setView("lobby")} 
          />
      )}


      <p style={{ marginTop: "2rem", fontSize: "0.8rem", color: "#666" }}>
        Base api url: {import.meta.env.VITE_GAME_API_BASE_URL}
      </p>
    </div>
  );
}
