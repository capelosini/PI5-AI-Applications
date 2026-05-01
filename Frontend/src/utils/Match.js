import Player from "./Player";
import Spectator from "./Spectator";
import Cell from "./Cell";

export default class Match {
    constructor(data) {
        this.id = data.id;
        this.status = data.status;
        this.turingPlayer = data.turing_player ? new Player(data.turing_player) : null;
        this.lovelacePlayer = data.lovelace_player ? new Player(data.lovelace_player) : null;
        this.spectators = Spectator.fromArray(data.spectators);
        this.board = Cell.fromBoard(data.board);
        this.currentTurnNumber = data.current_turn_number;
        this.currentTurnTeamId = data.current_turn_team_id;
        this.currentTurnPhase = data.current_turn_phase;
        this.winnerTeam = data.winner_team;
        this.winnerPlayerId = data.winner_player_id;
        this.lostPlayerId = data.lost_player_id;
        this.startedAt = data.started_at ? new Date(data.started_at) : null;
        this.finishedAt = data.finished_at ? new Date(data.finished_at) : null;
        this.createdAt = data.created_at ? new Date(data.created_at) : null;
        this.createdBy = data.created_by;
        this.autoStart = data.auto_start;
    }

    get shortId() {
        return this.id ? `${this.id.substring(0, 8)}...` : 'N/A';
    }

    get isWaiting() {
        return this.status === "WAITING_PLAYERS";
    }

    get isStarted() {
        return this.status === "STARTED";
    }

    get isFinished() {
        return this.status === "FINISHED";
    }

    get formattedStatus() {
        if (!this.status) return 'Unknown';
        return this.status.split('_').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
        ).join(' ');
    }

    get turingName() {
        return this.turingPlayer?.displayName || "Waiting...";
    }

    get lovelaceName() {
        return this.lovelacePlayer?.displayName || "Waiting...";
    }

    get winnerName() {
        if (!this.winnerTeam) return null;
        return this.winnerTeam === 1 ? this.turingName : this.lovelaceName;
    }

    static fromArray(dataArray) {
        if (!dataArray || !Array.isArray(dataArray)) return [];
        return dataArray.map(data => new Match(data));
    }
}
