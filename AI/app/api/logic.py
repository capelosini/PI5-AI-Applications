# app/api/logic.py
import os
import random
from typing import Optional

import torch

from app.core.constants import (
    ACTIONS_COMBINED,
    BOARD_SIZE,
    LEVEL_WIN,
    NAME_MAPPING,
    REVERSE_NAME_MAPPING,
    TEAM_ID,
    TEAMS,
)
from app.core.gameTorch import Game
from app.core.model import Model, device

from .schemas import Cell, PlayerTurnResponse, Position, SetupResponse

# Instância global do modelo
model_instance = None


def load_model():
    """Carrega o modelo AI se ainda não estiver carregado."""
    global model_instance
    if model_instance is None:
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        model_path = os.path.join(project_root, "checkpoints", "captcha_2.0_final.pth")

        model_instance = Model(board_size=BOARD_SIZE, actions_n=128).to(device)

        try:
            model_instance.load_state_dict(torch.load(model_path, map_location=device))
            model_instance.eval()
            print(f"[*] Modelo AI carregado de: {model_path}", flush=True)
        except Exception as e:
            print(
                f"[!] Erro ao carregar o modelo AI (Provavelmente incompatível com 0-index): {e}",
                flush=True,
            )
            model_instance = None


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
    if model_instance is None:
        # Fallback para jogada aleatória se o modelo não carregar
        return random_fallback(board, team_id)

    # 1. Converter o estado da API (já é 0-based) diretamente para o Game
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

    mask = game.get_valid_mask()
    if not mask.any():
        return None

    state_tensor = game.get_state_tensor().unsqueeze(0).to(device)
    with torch.no_grad():
        q_values = model_instance(state_tensor)
        q_values[0][~mask] = -1e9
        action_id = torch.argmax(q_values).item()

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
    """Fallback simples caso o modelo falhe."""
    print("Using fallback AI")
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
    valid_indices = torch.where(mask)[0]
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


load_model()
