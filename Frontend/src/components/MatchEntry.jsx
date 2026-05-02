import { useNavigate } from "react-router";

export default function MatchEntry({ match, onJoin }) {
    const navigate = useNavigate();

    return (
        <div className="match-card">
            <div className="match-info">
                <span className="match-id">ID: {match.shortId}</span>
                <span className={`match-status status-${match.status.toLowerCase()}`}>
                    {match.formattedStatus}
                </span>
            </div>
            <div className="match-players">
                <div className="player-slot">
                    <span className="team-label">Turing:</span>
                    <span className="player-name">{match.turingName}</span>
                </div>
                <div className="player-slot">
                    <span className="team-label">Lovelace:</span>
                    <span className="player-name">{match.lovelaceName}</span>
                </div>
            </div>
            <div className="match-actions" style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
                {match.isWaiting && (
                    <button 
                        className="btn btn-primary btn-sm" 
                        onClick={() => onJoin(match.id)}
                    >
                        Join
                    </button>
                )}
                <button 
                    className="btn btn-secondary btn-sm" 
                    onClick={() => navigate(`/spectate/${match.id}`)}
                >
                    Spectate
                </button>
            </div>
        </div>
    );
}
