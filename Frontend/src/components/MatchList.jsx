import MatchEntry from "./MatchEntry";

export default function MatchList({ matches, onJoin }) {
    if (!matches || matches.length === 0) {
        return (
            <div className="match-list-empty">
                <p>No active matches found.</p>
            </div>
        );
    }

    return (
        <div className="match-list-container">
            <h3>Active Matches</h3>
            <div className="match-list">
                {matches.map((match) => (
                    <MatchEntry 
                        key={match.id} 
                        match={match} 
                        onJoin={onJoin} 
                    />
                ))}
            </div>
        </div>
    );
}
