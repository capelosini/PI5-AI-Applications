import random

import torch

from .constants import (
    ACTIONS_COMBINED,
    BOARD_SIZE,
    LEVEL_BRICK,
    LEVEL_GROUND,
    LEVEL_WIN,
    MAX_LEVEL,
    PLAYERS_LIST,
    TEAM_ID,
    TEAMS,
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
        # 0=Ground, 3=Win, 4=Brick
        self.board = [
            [LEVEL_GROUND for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)
        ]
        self.status = "PLAYING"
        self.turn_team_id = 1
        self.turn_count = 0

        all_cells = [(y, x) for y in range(BOARD_SIZE) for x in range(BOARD_SIZE)]
        starting_pos = random.sample(all_cells, 4)

        for i, name in enumerate(PLAYERS_LIST):
            self.char_positions[name] = starting_pos[i]

    def get_valid_mask(self):
        mask = torch.zeros(128, dtype=torch.bool)
        current_team_name = TEAM_ID[self.turn_team_id]
        my_chars = TEAMS[current_team_name]

        for char_idx, char_name in enumerate(my_chars):
            y, x = self.char_positions[char_name]
            curr_level = self.board[y][x]

            for act_idx, act in enumerate(ACTIONS_COMBINED):
                my, mx = act["move"]
                ny, nx = y + my, x + mx

                if 0 <= ny < BOARD_SIZE and 0 <= nx < BOARD_SIZE:
                    target_level = self.board[ny][nx]

                    # Cannot move to a brick level
                    if target_level >= LEVEL_BRICK:
                        continue

                    is_occupied = any(
                        p == (ny, nx) for p in self.char_positions.values()
                    )

                    # Rule: currentCellLevel >= nextCellLevel - 1
                    if target_level <= (curr_level + 1) and not is_occupied:
                        uy, ux = act["upgrade"]
                        un_y, un_x = ny + uy, nx + ux

                        if 0 <= un_y < BOARD_SIZE and 0 <= un_x < BOARD_SIZE:
                            # Cannot upgrade a brick
                            if self.board[un_y][un_x] < LEVEL_BRICK:
                                # Rule: Cannot build on an occupied cell.
                                # - Cannot build on (ny, nx) because we just moved there.
                                # - Cannot build on any other character's position.
                                # - CAN build on (y, x) because we just left it.
                                is_upgrade_occupied = False
                                if (un_y, un_x) == (ny, nx):
                                    is_upgrade_occupied = True
                                else:
                                    for p_name, p_pos in self.char_positions.items():
                                        if p_name != char_name and p_pos == (
                                            un_y,
                                            un_x,
                                        ):
                                            is_upgrade_occupied = True
                                            break

                                if not is_upgrade_occupied:
                                    mask[char_idx * 64 + act_idx] = True

        return mask

    def get_state_tensor(self):
        tensor = torch.zeros((5, BOARD_SIZE, BOARD_SIZE))
        for y in range(BOARD_SIZE):
            for x in range(BOARD_SIZE):
                # Normalized (0.0 to 1.0)
                tensor[0, y, x] = self.board[y][x] / float(MAX_LEVEL)

        my_team = TEAMS[TEAM_ID[self.turn_team_id]]
        for i, name in enumerate(my_team):
            y, x = self.char_positions[name]
            tensor[1 + i, y, x] = 1.0

        enemy_team = TEAMS[TEAM_ID[3 - self.turn_team_id]]
        for i, name in enumerate(enemy_team):
            y, x = self.char_positions[name]
            tensor[3 + i, y, x] = 1.0

        return tensor

    def apply_action(self, action_id):
        reward = 0.0
        team_name = TEAM_ID[self.turn_team_id]
        char_names = TEAMS[team_name]
        enemy_team_name = TEAM_ID[3 - self.turn_team_id]
        enemy_chars = TEAMS[enemy_team_name]

        win_was_possible = self._check_if_win_possible(char_names)

        char_name = char_names[action_id // 64]
        action = ACTIONS_COMBINED[action_id % 64]
        old_pos = self.char_positions[char_name]

        ny, nx = old_pos[0] + action["move"][0], old_pos[1] + action["move"][1]
        old_level = self.board[old_pos[0]][old_pos[1]]
        new_level = self.board[ny][nx]
        self.char_positions[char_name] = (ny, nx)

        if new_level == LEVEL_WIN:
            self.status = "FINISHED"
            self.winner = team_name
            return 20.0

        if new_level > old_level:
            if new_level == 2:
                reward += 1.5
            elif new_level == 1:
                reward += 0.3

        if win_was_possible:
            reward -= 10.0

        uy, ux = ny + action["upgrade"][0], nx + action["upgrade"][1]
        self.board[uy][ux] += 1
        upgraded_level = self.board[uy][ux]

        for e_char in enemy_chars:
            ey, ex = self.char_positions[e_char]
            e_level = self.board[ey][ex]
            dist = max(abs(ey - uy), abs(ex - ux))

            if dist <= 1:
                if upgraded_level == LEVEL_WIN and e_level == 2:
                    reward -= 8.0
                elif upgraded_level == 2 and e_level == 1:
                    reward -= 2.0
                elif upgraded_level == LEVEL_BRICK and e_level == 2:
                    reward += 1.0

        for m_char in char_names:
            my, mx = self.char_positions[m_char]
            m_level = self.board[my][mx]
            dist = max(abs(my - uy), abs(mx - ux))
            if dist <= 1 and upgraded_level == LEVEL_WIN and m_level == 2:
                reward += 1.0

        self.turn_team_id = 3 - self.turn_team_id
        self.turn_count += 1

        enemy_mask = self.get_valid_mask()
        if not enemy_mask.any():
            reward += 20.0
            self.status = "FINISHED"
            self.winner = team_name

        for e_char in enemy_chars:
            ey, ex = self.char_positions[e_char]
            if self.board[ey][ex] == LEVEL_WIN - 1:
                reward -= 0.5

        turn_penalty = -0.05
        if self.turn_count > 40:
            turn_penalty = -0.2

        return reward + turn_penalty

    def _check_if_win_possible(self, char_names):
        mask = self.get_valid_mask()
        valid_indices = torch.where(mask)[0]

        for idx in valid_indices:
            c_idx = idx // 64
            a_idx = idx % 64
            char_name = char_names[c_idx]
            move_offset = ACTIONS_COMBINED[a_idx]["move"]

            curr_y, curr_x = self.char_positions[char_name]
            target_y = curr_y + move_offset[0]
            target_x = curr_x + move_offset[1]

            if self.board[target_y][target_x] == LEVEL_WIN:
                return True
        return False

    def render(self):
        symbols = {0: " . ", 1: " o ", 2: " O ", 3: " # ", 4: " X "}
        char_map = {}
        for i, name in enumerate(TEAMS["turing"]):
            char_map[self.char_positions[name]] = f"T{i + 1}"
        for i, name in enumerate(TEAMS["lovelace"]):
            char_map[self.char_positions[name]] = f"L{i + 1}"

        print("\n   0  1  2  3  4")
        for y in range(BOARD_SIZE):
            row_str = f"{y} "
            for x in range(BOARD_SIZE):
                if (y, x) in char_map:
                    row_str += f"[{char_map[(y, x)]}] "
                else:
                    row_str += symbols[self.board[y][x]]
            print(row_str)
        print("-" * 20)
