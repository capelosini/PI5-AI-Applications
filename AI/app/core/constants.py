# app/core/constants.py
import torch

BOARD_SIZE = 5
DIRECTIONS = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]
PLAYERS_LIST = ["beatriz", "karin", "claro", "rey"]
TEAMS = {
    "lovelace": [PLAYERS_LIST[0], PLAYERS_LIST[1]],  # Team 2
    "turing": [PLAYERS_LIST[2], PLAYERS_LIST[3]],  # Team 1
}
TEAM_ID = {1: "turing", 2: "lovelace"}

# Precompute combined actions (64 combinations)
ACTIONS_COMBINED = []
for m_idx in range(8):
    for u_idx in range(8):
        ACTIONS_COMBINED.append(
            {"move": DIRECTIONS[m_idx], "upgrade": DIRECTIONS[u_idx]}
        )

# API Specific Mappings
TEAM_PROFESSORS = {
    1: ["CLARO", "REY"],  # Turing
    2: ["KARIN", "BEATRIZ"],  # Lovelace
}

NAME_MAPPING = {
    "CLARO": "claro",
    "REY": "rey",
    "KARIN": "karin",
    "BEATRIZ": "beatriz",
}
REVERSE_NAME_MAPPING = {v: k for k, v in NAME_MAPPING.items()}

# Game Levels (0-based)
LEVEL_GROUND = 0
LEVEL_WIN = 3
LEVEL_BRICK = 4
MAX_LEVEL = 4
