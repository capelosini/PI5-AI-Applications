import random

import torch
from game import ACTIONS_COMBINED, BOARD_SIZE, TEAM_ID, Game
from model import Model

# --- Simple Simulation Loop ---
game = Game()
game.start()

model = Model(BOARD_SIZE, len(ACTIONS_COMBINED) * len(TEAM_ID))

while game.status == "PLAYING":
    mask = game.get_valid_mask()
    valid_indices = torch.where(mask)[0]

    if len(valid_indices) == 0:
        print(f"Team {TEAM_ID[game.turn_team_id]} has no moves! Stalemate.")
        break

    # Pick a random valid action
    action_to_take = random.choice(valid_indices.tolist())
    game.apply_action(action_to_take)

    print(game.board)
    print(game.char_positions)
    print("\n-=-=-=-=\n")

print(f"Game Over! Winner: {game.winner}")
