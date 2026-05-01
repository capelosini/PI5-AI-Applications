export default class Spectator {
    constructor(data) {
        this.id = data.id;
        this.gameId = data.game_id;
        this.name = data.spectator_name;
        this.avatar = data.spectator_avatar;
        this.createdAt = data.created_at ? new Date(data.created_at) : null;
        this.accessToken = data.spectator_access_token; // Only present on register
    }

    static fromArray(dataArray) {
        if (!dataArray || !Array.isArray(dataArray)) return [];
        return dataArray.map(data => new Spectator(data));
    }
}
