# app/api/logic.py
import os
import random
from typing import Optional
import numpy as np

from app.core.constants import (
    ACTIONS_COMBINED,
    BOARD_SIZE,
    LEVEL_WIN,
    NAME_MAPPING,
    REVERSE_NAME_MAPPING,
    TEAM_ID,
    TEAMS,
)
from app.core.gameNumpy import Game
from app.core.minimax_iterative import iterative_deepening_minimax

from .schemas import Cell, PlayerTurnResponse, Position, SetupResponse


def choose_setup(board: list[list[Cell]]) -> SetupResponse:
    candidates = [
        (r, c)
        for r in range(BOARD_SIZE)
        for c in range(BOARD_SIZE)
        if board[r][c].level == 0 and board[r][c].professor is None
    ]
    if not candidates:
        candidates = [
            (r, c)
            for r in range(BOARD_SIZE)
            for c in range(BOARD_SIZE)
            if board[r][c].professor is None
        ]

    row, col = random.choice(candidates) if candidates else (0, 0)
    return SetupResponse(row=row, col=col)


def choose_turn(board: list[list[Cell]], team_id: int) -> Optional[PlayerTurnResponse]:
    # 1. Convert the state from the API (0-based) directly to the Game state format
    ai_board = [[cell.level for cell in row] for row in board]
    char_positions = {}

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            cell = board[r][c]
            if cell.professor:
                prof_name = cell.professor.upper()
                if prof_name in NAME_MAPPING:
                    char_positions[NAME_MAPPING[prof_name]] = (r, c)

    current_team_name = TEAM_ID.get(team_id)
    if not current_team_name:
        return None

    game = Game()
    game.board = ai_board
    game.char_positions = char_positions
    game.turn_team_id = team_id

    # 2. Check if we have valid moves
    mask = game.get_valid_mask()
    if not np.any(mask):
        return None

    try:
        # Run iterative deepening minimax search with a safe time limit (e.g. 3.8 seconds)
        action_id, depth = iterative_deepening_minimax(game, team_id, time_limit=3.8)
        if action_id is None:
            return random_fallback(board, team_id)
    except Exception as e:
        print(f"[!] Error running Minimax search: {e}", flush=True)
        return random_fallback(board, team_id)

    my_chars = TEAMS[current_team_name]
    char_name = my_chars[action_id // 64]
    action = ACTIONS_COMBINED[action_id % 64]

    curr_y, curr_x = char_positions[char_name]
    dst_y, dst_x = curr_y + action["move"][0], curr_x + action["move"][1]
    men_y, men_x = dst_y + action["upgrade"][0], dst_x + action["upgrade"][1]

    return PlayerTurnResponse(
        professor=REVERSE_NAME_MAPPING[char_name],
        move_to=Position(row=dst_y, col=dst_x),
        mentor_at=Position(row=men_y, col=men_x),
    )


def random_fallback(
    board: list[list[Cell]], team_id: int
) -> Optional[PlayerTurnResponse]:
    """Simple fallback if minimax search fails."""
    print("Using fallback AI", flush=True)
    ai_board = [[cell.level for cell in row] for row in board]
    char_positions = {}
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c].professor:
                prof_name = board[r][c].professor.upper()
                if prof_name in NAME_MAPPING:
                    char_positions[NAME_MAPPING[prof_name]] = (r, c)

    game = Game()
    game.board = ai_board
    game.char_positions = char_positions
    game.turn_team_id = team_id
    mask = game.get_valid_mask()
    valid_indices = np.where(mask)[0]
    if len(valid_indices) == 0:
        return None

    action_id = random.choice(valid_indices.tolist())
    current_team_name = TEAM_ID[team_id]
    my_chars = TEAMS[current_team_name]
    char_name = my_chars[action_id // 64]
    action = ACTIONS_COMBINED[action_id % 64]
    curr_y, curr_x = char_positions[char_name]
    dst_y, dst_x = curr_y + action["move"][0], curr_x + action["move"][1]
    men_y, men_x = dst_y + action["upgrade"][0], dst_x + action["upgrade"][1]

    return PlayerTurnResponse(
        professor=REVERSE_NAME_MAPPING[char_name],
        move_to=Position(row=dst_y, col=dst_x),
        mentor_at=Position(row=men_y, col=men_x),
    )
