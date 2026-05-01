import { useState } from "react";
import AccountManager from "@/utils/AccountManager";
import { API } from "@/utils/API";

const TEAM_NAME = "HoneyPot";

export default function AccountManagement({ onAccountChange, onCancel }) {
    const [accounts, setAccounts] = useState(AccountManager.getAccounts());
    const [view, setView] = useState("list"); // "list", "create", "edit"
    const [editingPlayer, setEditingPlayer] = useState(null);
    const [newPlayerData, setNewPlayerData] = useState({
        group_name: TEAM_NAME,
        ai_player_name: "",
        ai_player_avatar: "",
        ai_player_description: "",
        ai_player_move_endpoint: ""
    });
    const [editMoveEndpoint, setEditMoveEndpoint] = useState("");

    const activePlayer = AccountManager.getActivePlayer();

    const handleCreatePlayer = async (e) => {
        e.preventDefault();
        try {
            const player = await API.players.create(newPlayerData);
            AccountManager.saveAccount(player);
            setAccounts(AccountManager.getAccounts());
            setView("list");
            setNewPlayerData({ 
                group_name: TEAM_NAME, 
                ai_player_name: "", 
                ai_player_avatar: "",
                ai_player_description: "", 
                ai_player_move_endpoint: "" 
            });
        } catch (err) {
            alert("Error creating player: " + err.message);
        }
    };

    const handleStartEdit = (player) => {
        setEditingPlayer(player);
        setEditMoveEndpoint(player.aiPlayerMoveEndpoint || "");
        setView("edit");
    };

    const handleUpdatePlayer = async (e) => {
        e.preventDefault();
        try {
            // We need to set the auth token temporarily to update the endpoint
            // or ensure the active player is the one being edited.
            const originalToken = activePlayer?.accessToken;
            setAuthToken(editingPlayer.accessToken);
            
            const updatedPlayer = await API.players.updateEndpoint(editingPlayer.id, {
                ai_player_move_endpoint: editMoveEndpoint
            });
            
            // Restore original token if needed
            setAuthToken(originalToken);

            // Update local storage
            const fullUpdatedPlayer = { ...editingPlayer, aiPlayerMoveEndpoint: updatedPlayer.aiPlayerMoveEndpoint };
            AccountManager.saveAccount(fullUpdatedPlayer);
            
            // Update active player state if we edited the active one
            if (activePlayer?.id === editingPlayer.id) {
                onAccountChange();
            }

            setAccounts(AccountManager.getAccounts());
            setView("list");
            alert("Endpoint updated successfully!");
        } catch (err) {
            alert("Error updating endpoint: " + err.message);
        }
    };

    const handleLogin = (playerId) => {
        AccountManager.setActivePlayer(playerId);
        onAccountChange();
    };

    const handleExport = () => {
        AccountManager.exportAccounts();
    };

    const handleImport = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        try {
            await AccountManager.importAccounts(file);
            setAccounts(AccountManager.getAccounts());
            alert("Accounts imported successfully!");
        } catch (err) {
            alert("Error importing accounts: " + err.message);
        }
    };

    return (
        <div className="account-container">
            <h2>Account Management</h2>
            
            {view === "list" && (
                <>
                    <div className="account-list">
                        {accounts.length === 0 ? (
                            <p className="empty-msg">No accounts found. Create one to get started.</p>
                        ) : (
                            accounts.map(acc => (
                                <div key={acc.id} className={`account-item ${activePlayer?.id === acc.id ? 'active' : ''}`}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                                        {acc.aiPlayerAvatar && (
                                            <img 
                                                src={acc.aiPlayerAvatar} 
                                                alt={acc.aiPlayerName} 
                                                className="acc-avatar"
                                            />
                                        )}
                                        <div className="acc-info">
                                            <span className="acc-name">{acc.aiPlayerName || acc.groupName}</span>
                                            <span className="acc-group">{acc.groupName}</span>
                                        </div>
                                    </div>
                                    <div className="acc-actions">
                                        <button 
                                            className="btn btn-secondary btn-sm" 
                                            onClick={() => handleStartEdit(acc)}
                                            style={{ marginRight: '0.5rem' }}
                                        >
                                            Edit
                                        </button>
                                        <button 
                                            className="btn btn-primary btn-sm" 
                                            onClick={() => handleLogin(acc.id)}
                                            disabled={activePlayer?.id === acc.id}
                                        >
                                            {activePlayer?.id === acc.id ? 'Logged In' : 'Login'}
                                        </button>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>

                    <div className="button-group" style={{ marginTop: '2rem' }}>
                        <button className="btn btn-primary" onClick={() => setView("create")}>
                            Create New Player
                        </button>
                        <div className="secondary-actions">
                            <button className="btn btn-secondary" onClick={handleExport}>
                                Export Accounts
                            </button>
                            <label className="btn btn-secondary">
                                Import Accounts
                                <input type="file" accept=".json" onChange={handleImport} style={{ display: 'none' }} />
                            </label>
                        </div>
                        <button className="btn btn-secondary" onClick={onCancel}>
                            Back to Lobby
                        </button>
                    </div>
                </>
            )}

            {view === "create" && (
                <form className="config-form" onSubmit={handleCreatePlayer}>
                    <h3>Create Player</h3>
                    <div className="form-group">
                        <label>AI Player Name</label>
                        <input 
                            type="text" 
                            value={newPlayerData.ai_player_name} 
                            onChange={e => setNewPlayerData({...newPlayerData, ai_player_name: e.target.value})}
                        />
                    </div>
                    <div className="form-group">
                        <label>AI Player Avatar (URL)</label>
                        <input 
                            type="url" 
                            value={newPlayerData.ai_player_avatar} 
                            onChange={e => setNewPlayerData({...newPlayerData, ai_player_avatar: e.target.value})}
                            placeholder="https://example.com/avatar.png"
                        />
                    </div>
                    <div className="form-group">
                        <label>AI Description</label>
                        <textarea 
                            value={newPlayerData.ai_player_description} 
                            onChange={e => setNewPlayerData({...newPlayerData, ai_player_description: e.target.value})}
                            style={{ backgroundColor: '#2a2a32', color: 'white', border: '1px solid #444', borderRadius: '6px', padding: '0.8rem' }}
                        />
                    </div>
                    <div className="form-group">
                        <label>Move Endpoint URL</label>
                        <input 
                            type="url" 
                            value={newPlayerData.ai_player_move_endpoint} 
                            onChange={e => setNewPlayerData({...newPlayerData, ai_player_move_endpoint: e.target.value})}
                        />
                    </div>
                    <div className="button-group" style={{ marginTop: '1.5rem' }}>
                        <button type="submit" className="btn btn-primary">Create</button>
                        <button type="button" className="btn btn-secondary" onClick={() => setView("list")}>Cancel</button>
                    </div>
                </form>
            )}

            {view === "edit" && (
                <form className="config-form" onSubmit={handleUpdatePlayer}>
                    <h3>Edit Move Endpoint</h3>
                    <p style={{ fontSize: '0.9rem', color: '#aaa', marginBottom: '1rem' }}>
                        Updating endpoint for: <strong>{editingPlayer?.aiPlayerName || editingPlayer?.groupName}</strong>
                    </p>
                    <div className="form-group">
                        <label>Move Endpoint URL</label>
                        <input 
                            type="url" 
                            value={editMoveEndpoint} 
                            onChange={e => setEditMoveEndpoint(e.target.value)}
                            placeholder="https://your-ai-api.com/move"
                            required
                        />
                    </div>
                    <div className="button-group" style={{ marginTop: '1.5rem' }}>
                        <button type="submit" className="btn btn-primary">Update</button>
                        <button type="button" className="btn btn-secondary" onClick={() => setView("list")}>Cancel</button>
                    </div>
                </form>
            )}
        </div>
    );
}
