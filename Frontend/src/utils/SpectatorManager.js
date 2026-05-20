export default class SpectatorManager {
    static STORAGE_KEY = 'pi5_spectator_sessions';

    static getSessions() {
        const stored = localStorage.getItem(this.STORAGE_KEY);
        try {
            return stored ? JSON.parse(stored) : {};
        } catch (e) {
            console.error("Failed to parse spectator sessions:", e);
            return {};
        }
    }

    static getSession(gameId) {
        const sessions = this.getSessions();
        return sessions[gameId] || null;
    }

    static saveSession(gameId, token) {
        const sessions = this.getSessions();
        sessions[gameId] = token;
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(sessions));
    }

    static removeSession(gameId) {
        const sessions = this.getSessions();
        delete sessions[gameId];
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(sessions));
    }
}
