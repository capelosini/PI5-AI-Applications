export default class Player {
    constructor(data) {
        this.id = data.id;
        this.groupName = data.group_name;
        this.aiPlayerName = data.ai_player_name;
        this.aiPlayerAvatar = data.ai_player_avatar;
        this.aiPlayerDescription = data.ai_player_description;
        this.aiPlayerMoveEndpoint = data.ai_player_move_endpoint;
        this.gamesPlayed = data.games_played || 0;
        this.gamesWon = data.games_won || 0;
        this.gamesLost = data.games_lost || 0;
        this.averageMoveTime = data.average_move_time;
        this.accessToken = data.player_access_token; // Only present on create
    }

    get displayName() {
        return this.aiPlayerName || this.groupName || "Anonymous Player";
    }

    get winRate() {
        if (!this.gamesPlayed) return 0;
        return ((this.gamesWon / this.gamesPlayed) * 100).toFixed(1);
    }

    static fromArray(dataArray) {
        if (!dataArray || !Array.isArray(dataArray)) return [];
        return dataArray.map(data => new Player(data));
    }
}
