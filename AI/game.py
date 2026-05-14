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
        self.turn_count = 0
        self.status = "PLAYING"
        self.winner = None

    def start(self):
        # Initialize board with level 1
        self.board = [[1 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.status = "PLAYING"
        self.turn_team_id = 1
        self.turn_count = 0

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

    def _check_if_win_possible(self, char_names):
        """
        Scans all valid moves for the specified characters to see if any
        lead to a Level 4 (Winning) cell.
        """
        mask = self.get_valid_mask()
        # Indices are structured as: [char_0_actions... char_1_actions...]
        valid_indices = torch.where(mask)[0]

        for idx in valid_indices:
            # Determine which character this action belongs to (0 or 1)
            c_idx = idx // 64
            # Get the specific action ID (0-63)
            a_idx = idx % 64

            char_name = char_names[c_idx]
            move_offset = ACTIONS_COMBINED[a_idx]["move"]

            # Calculate target position
            curr_y, curr_x = self.char_positions[char_name]
            target_y = curr_y + move_offset[0]
            target_x = curr_x + move_offset[1]

            # Check if the target cell is a Level 4
            if self.board[target_y][target_x] == 4:
                return True

        return False

    def apply_action(self, action_id):
        reward = 0.0
        team_name = TEAM_ID[self.turn_team_id]
        char_names = TEAMS[team_name]
        enemy_team_name = TEAM_ID[3 - self.turn_team_id]

        # 1. Kill Instinct Check
        win_was_possible = self._check_if_win_possible(char_names)

        # 2. Execute Move
        char_name = char_names[action_id // 64]
        action = ACTIONS_COMBINED[action_id % 64]
        old_pos = self.char_positions[char_name]

        ny, nx = old_pos[0] + action["move"][0], old_pos[1] + action["move"][1]
        new_level = self.board[ny][nx]
        self.char_positions[char_name] = (ny, nx)

        # 3. Check Win Condition (Immediate Win)
        if new_level == 4:
            self.status = "FINISHED"
            self.winner = team_name
            return 30.0

        # 4. Movement Rewards
        if new_level > self.board[old_pos[0]][old_pos[1]]:
            reward += 0.5

        if win_was_possible:
            reward -= 15.0  # Heavy penalty for missing the kill

        # 5. Execute Upgrade
        uy, ux = ny + action["upgrade"][0], nx + action["upgrade"][1]
        self.board[uy][ux] += 1
        upgraded_level = self.board[uy][ux]

        # 6. Honeypot Upgrade Logic | Trapping
        for e_char in TEAMS[enemy_team_name]:
            ey, ex = self.char_positions[e_char]
            if abs(ey - uy) <= 1 and abs(ex - ux) <= 1:
                # FIXED LOGIC ORDER: Check the most specific/dangerous condition first
                if upgraded_level == 4:
                    reward -= 5.0  # Highly risky to give them a Level 4 goal!
                elif upgraded_level == 3:
                    reward += 3.5  # Excellent! Blocking an enemy with a high cell.

        # 7. Switch Turn & Check for Total Trap
        self.turn_team_id = 3 - self.turn_team_id
        self.turn_count += 1

        enemy_mask = self.get_valid_mask()
        if not enemy_mask.any():
            reward += 15.0  # (Optional) Boosted to ensure trapping is deeply valued
            self.status = "FINISHED"
            self.winner = team_name

        # 8. Dynamic Turn Penalty
        turn_penalty = -0.1
        if self.turn_count > 30:
            turn_penalty = -0.5  # Make it "painful" to keep playing without winning

        return reward + turn_penalty

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

    def render(self):
        # Mapping cell levels to symbols
        symbols = {1: " . ", 2: " o ", 3: " O ", 4: " # "}

        # Create a name-to-team mapping for display
        # T1, T2 for Turing; L1, L2 for Lovelace
        char_map = {}
        for i, name in enumerate(TEAMS["turing"]):
            char_map[self.char_positions[name]] = f"T{i + 1}"
        for i, name in enumerate(TEAMS["lovelace"]):
            char_map[self.char_positions[name]] = f"L{i + 1}"

        print("\n   0  1  2  3  4")  # Column headers
        for y in range(BOARD_SIZE):
            row_str = f"{y} "  # Row header
            for x in range(BOARD_SIZE):
                if (y, x) in char_map:
                    row_str += f"[{char_map[(y, x)]}] "
                else:
                    row_str += symbols[self.board[y][x]]
            print(row_str)
        print("-" * 20)
