import Match from "./Match";
import Player from "./Player";
import Spectator from "./Spectator";

const BASE_URL = import.meta.env.VITE_GAME_API_BASE_URL;

let AUTH_TOKEN = null;

export const setAuthToken = (token) => {
    AUTH_TOKEN = token;
};

async function request(path, options = {}) {
    const url = `${BASE_URL}${path}`;
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
    };

    if (AUTH_TOKEN) {
        headers['Authorization'] = `Bearer ${AUTH_TOKEN}`;
    }

    const response = await fetch(url, {
        ...options,
        headers,
    });


  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `HTTP error! status: ${response.status}`);
  }

  if (response.status === 204) return null;
  return response.json();
}

export const API = {
  games: {
    list: async (params = {}) => {
      const query = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) query.append(key, value);
      });
      const data = await request(`/games?${query.toString()}`);
      return {
        ...data,
        items: Match.fromArray(data.items),
      };
    },
    create: async (data) => {
      const result = await request("/games", {
        method: "POST",
        body: JSON.stringify(data),
      });
      return new Match(result);
    },
    get: async (gameId) => {
      const result = await request(`/games/${gameId}`);
      return new Match(result);
    },
    join: async (gameId, data) => {
      const result = await request(`/games/${gameId}/join`, {
        method: "POST",
        body: JSON.stringify(data),
      });
      return new Match(result);
    },
    start: async (gameId, data = null) => {
      const result = await request(`/games/${gameId}/start`, {
        method: "POST",
        body: JSON.stringify(data),
      });
      return new Match(result);
    },
    addSpectator: async (gameId, data) => {
      const result = await request(`/games/${gameId}/spectators`, {
        method: "POST",
        body: JSON.stringify(data),
      });
      return new Spectator(result);
    },
  },
  players: {
    list: async () => {
      const data = await request("/players");
      return Player.fromArray(data);
    },
    create: async (data) => {
      const result = await request("/players", {
        method: "POST",
        body: JSON.stringify(data),
      });
      return new Player(result);
    },
    updateEndpoint: async (playerId, data) => {
      const result = await request(`/players/${playerId}`, {
        method: "PUT",
        body: JSON.stringify(data),
      });
      return new Player(result);
    },
  },
  dev: {
    mockState: (data = null) =>
      request("/games/mock-state", {
        method: "POST",
        body: JSON.stringify(data),
      }),
  },
};
