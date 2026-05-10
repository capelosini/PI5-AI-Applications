import random

import torch

# Configuration
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


class Game:
    def __init__(self):
        self.board = None  # 5x5 grid of levels
        self.char_positions = {}  # name -> (y, x)
        self.turn_team_id = 1
        self.status = "PLAYING"
        self.winner = None

    def start(self):
        # Initialize board with level 1
        self.board = [[1 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.status = "PLAYING"
        self.turn_team_id = 1

        # Randomly place characters on unique cells
        all_cells = [(y, x) for y in range(BOARD_SIZE) for x in range(BOARD_SIZE)]
        starting_pos = random.sample(all_cells, 4)

        for i, name in enumerate(PLAYERS_LIST):
            self.char_positions[name] = starting_pos[i]

    def get_valid_mask(self):
        """Returns a boolean array of size 128 (64 actions * 2 characters)"""
        mask = torch.zeros(128, dtype=torch.bool)
        current_team_name = TEAM_ID[self.turn_team_id]
        my_chars = TEAMS[current_team_name]

        for char_idx, char_name in enumerate(my_chars):
            y, x = self.char_positions[char_name]
            curr_level = self.board[y][x]

            for act_idx, act in enumerate(ACTIONS_COMBINED):
                # 1. Check Move Validity
                my, mx = act["move"]
                ny, nx = y + my, x + mx

                if 0 <= ny < BOARD_SIZE and 0 <= nx < BOARD_SIZE:
                    target_level = self.board[ny][nx]

                    # Rule: currentCellLevel >= nextCellLevel - 1
                    # Rule: Cell cannot be occupied by another character
                    is_occupied = any(
                        p == (ny, nx) for p in self.char_positions.values()
                    )

                    if target_level <= (curr_level + 1) and not is_occupied:
                        # 2. Check Upgrade Validity
                        uy, ux = act["upgrade"]
                        un_y, un_x = ny + uy, nx + ux

                        if 0 <= un_y < BOARD_SIZE and 0 <= un_x < BOARD_SIZE:
                            if (
                                self.board[un_y][un_x] < 4
                            ):  # Cannot upgrade past level 4
                                mask[char_idx * 64 + act_idx] = True
        return mask

    def apply_action(self, action_id):
        reward = 0.0

        # 1. Identify current state info
        team_name = TEAM_ID[self.turn_team_id]
        char_name = TEAMS[team_name][action_id // 64]
        old_y, old_x = self.char_positions[char_name]
        old_level = self.board[old_y][old_x]

        # 2. Execute Move
        action = ACTIONS_COMBINED[action_id % 64]
        ny, nx = old_y + action["move"][0], old_x + action["move"][1]
        new_level = self.board[ny][nx]

        self.char_positions[char_name] = (ny, nx)

        # Reward for climbing
        if new_level > old_level:
            reward += 0.5

        # 3. Check Win Condition
        if new_level == 4:
            self.status = "FINISHED"
            self.winner = team_name
            return 10.0  # Big win reward

        # 4. Execute Upgrade
        uy, ux = ny + action["upgrade"][0], nx + action["upgrade"][1]
        self.board[uy][ux] += 1

        # Reward for creating a path for yourself or blocking
        if self.board[uy][ux] == 4:
            reward += 0.2  # Strategic placement

        # 5. Switch Turn
        self.turn_team_id = 3 - self.turn_team_id

        return reward - 0.01  # Small step penalty to discourage aimless wandering

    def get_state_tensor(self):
        """Returns a (3, 5, 5) tensor for PyTorch RL"""
        tensor = torch.zeros((3, BOARD_SIZE, BOARD_SIZE))

        # Channel 0: Levels (Normalized)
        for y in range(BOARD_SIZE):
            for x in range(BOARD_SIZE):
                tensor[0, y, x] = self.board[y][x] / 4.0

        # Channel 1: My Characters
        my_team = TEAMS[TEAM_ID[self.turn_team_id]]
        for name in my_team:
            y, x = self.char_positions[name]
            tensor[1, y, x] = 1.0

        # Channel 2: Enemy Characters
        enemy_team = TEAMS[TEAM_ID[3 - self.turn_team_id]]
        for name in enemy_team:
            y, x = self.char_positions[name]
            tensor[2, y, x] = 1.0

        return tensor
