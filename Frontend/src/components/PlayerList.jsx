import { useState, useEffect } from "react";
import { API } from "@/utils/API";

export default function PlayerList({ onCancel }) {
    const [players, setPlayers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchPlayers = async () => {
            try {
                const data = await API.players.list();
                setPlayers(data);
            } catch (err) {
                setError("Failed to load players.");
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchPlayers();
    }, []);

    return (
        <div className="player-list-container">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <h2 style={{ margin: 0, color: '#ff4d4d' }}>Registered Players</h2>
                <button className="btn btn-secondary btn-sm" onClick={onCancel}>Back</button>
            </div>

            {loading ? (
                <p>Loading players...</p>
            ) : error ? (
                <p style={{ color: '#ff4d4d' }}>{error}</p>
            ) : (
                <div className="player-grid">
                    {players.map(player => (
                        <div key={player.id} className="player-card">
                            <div className="player-card-header">
                                {player.aiPlayerAvatar ? (
                                    <img src={player.aiPlayerAvatar} alt="" className="player-avatar-lg" />
                                ) : (
                                    <div className="player-avatar-placeholder" />
                                )}
                                <div className="player-card-info">
                                    <span className="player-card-name">{player.displayName}</span>
                                    <span className="player-card-group">{player.groupName}</span>
                                </div>
                            </div>
                            <div className="player-stats">
                                <div className="stat-item">
                                    <span className="stat-label">Wins</span>
                                    <span className="stat-value">{player.gamesWon}</span>
                                </div>
                                <div className="stat-item">
                                    <span className="stat-label">Lost</span>
                                    <span className="stat-value">{player.gamesLost}</span>
                                </div>
                                <div className="stat-item">
                                    <span className="stat-label">Rate</span>
                                    <span className="stat-value">{player.winRate}%</span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
