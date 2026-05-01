export default function MatchEntry({ match, onJoin }) {
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
            {match.isWaiting && (
                <button 
                    className="btn btn-primary btn-sm" 
                    onClick={() => onJoin(match.id)}
                >
                    Join
                </button>
            )}
        </div>
    );
}
