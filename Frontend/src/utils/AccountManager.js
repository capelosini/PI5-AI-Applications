export default class AccountManager {
    static STORAGE_KEY = 'pi5_player_accounts';
    static ACTIVE_PLAYER_KEY = 'pi5_active_player_id';

    static getAccounts() {
        const stored = localStorage.getItem(this.STORAGE_KEY);
        return stored ? JSON.parse(stored) : [];
    }

    static saveAccount(playerData) {
        const accounts = this.getAccounts();
        const existingIndex = accounts.findIndex(a => a.id === playerData.id);
        
        if (existingIndex > -1) {
            accounts[existingIndex] = playerData;
        } else {
            accounts.push(playerData);
        }
        
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(accounts));
    }

    static getActivePlayer() {
        const activeId = localStorage.getItem(this.ACTIVE_PLAYER_KEY);
        if (!activeId) return null;
        
        const accounts = this.getAccounts();
        return accounts.find(a => a.id.toString() === activeId) || null;
    }

    static setActivePlayer(playerId) {
        localStorage.setItem(this.ACTIVE_PLAYER_KEY, playerId.toString());
    }

    static logout() {
        localStorage.removeItem(this.ACTIVE_PLAYER_KEY);
    }

    static exportAccounts() {
        const accounts = this.getAccounts();
        const blob = new Blob([JSON.stringify(accounts, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `pi5_accounts_${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        URL.revokeObjectURL(url);
    }

    static async importAccounts(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                try {
                    const imported = JSON.parse(e.target.result);
                    if (!Array.isArray(imported)) throw new Error("Invalid format");
                    
                    const current = this.getAccounts();
                    // Merge by ID
                    const merged = [...current];
                    imported.forEach(imp => {
                        const idx = merged.findIndex(m => m.id === imp.id);
                        if (idx > -1) merged[idx] = imp;
                        else merged.push(imp);
                    });
                    
                    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(merged));
                    resolve(merged);
                } catch (err) {
                    reject(err);
                }
            };
            reader.readAsText(file);
        });
    }
}
