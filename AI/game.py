import json
import os
import random

import dotenv
import requests
import torch

dotenv.load_dotenv()
GAME_API_URL = os.getenv("GAME_API_URL")
BOT_TOKEN = os.getenv("BOT_TOKEN")

DIRECTIONS = [
    (-1, 0),  # 0: North
    (-1, 1),  # 1: North-East
    (0, 1),  # 2: East
    (1, 1),  # 3: South-East
    (1, 0),  # 4: South
    (1, -1),  # 5: South-West
    (0, -1),  # 6: West
    (-1, -1),  # 7: North-West
]

BOARD_SIZE = 5
PLAYERS_LIST = ["beatriz", "karin", "claro", "rey"]
TEAMS = {
    "lovelace": [PLAYERS_LIST[0], PLAYERS_LIST[1]],
    "turing": [PLAYERS_LIST[2], PLAYERS_LIST[3]],
}
CURRENT_TEAM = "turing"

actionsArray = []

for moveIdx in range(8):
    for upgradeIdx in range(8):
        moveOffset = DIRECTIONS[moveIdx]
        upgradeOffset = DIRECTIONS[upgradeIdx]

        actionsArray.append({"move": moveOffset, "upgrade": upgradeOffset})

actionsN = len(actionsArray)


class Game:
    def __init__(self):
        self.state = None
        self.session = requests.Session()
        self.session.headers.update(
            {"Authorization": f"Bearer {BOT_TOKEN}", "Content-Type": "application/json"}
        )

    def start(self):
        self.state = {
            "game_id": "9b4e3559-fd27-4d3a-a9f5-b58f3362443c",
            "status": "PLAYING",
            "winner_team": None,
            "turn_number": random.randint(1, 2),
            "turn_team_id": 1,
            "turn_phase": "player_turn",
            "board": self.generateStartBoard(),
            "last_action": None,
        }

    def generateStartBoard(self):
        board = []
        for row in range(BOARD_SIZE):
            board.append([])
            for cell in range(BOARD_SIZE):
                board[row].append({"level": 0, "professor": None})
        for i in range(4):
            board[random.randint(0, BOARD_SIZE - 1)][random.randint(0, BOARD_SIZE - 1)][
                "professor"
            ] = PLAYERS_LIST[i]
        return board

    def formatBoard(self, board):
        formated = torch.zeros((BOARD_SIZE * BOARD_SIZE, 2), dtype=torch.float32)
        for row in range(BOARD_SIZE):
            for cell in range(BOARD_SIZE):
                formated[row * BOARD_SIZE + cell][0] = board[row][cell]["level"]
                formated[row * BOARD_SIZE + cell][1] = (
                    0
                    if board[row][cell]["professor"] is None
                    else (
                        1
                        if board[row][cell]["professor"].lower() in TEAMS[CURRENT_TEAM]
                        else 2
                    )
                )

        return formated

    def getMockState(self, currentState=None):
        if GAME_API_URL is None:
            return {}
        response = self.session.post(
            GAME_API_URL + "/games/mock-state",
            data=json.dumps(currentState) if currentState else None,
        )
        self.state = response.json()
