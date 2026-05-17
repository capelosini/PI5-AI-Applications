import asyncio
import random
from datetime import date

from fastapi import FastAPI
from logic import choose_setup, choose_turn
from schemas import AITurnRequest, TurnPhase

app = FastAPI(
    title="CAPTCHA 2.0",
    description="CAPTCHA 2.0 AI for PI5",
    version="0.1.0",
)


@app.get("/health")
async def health():
    return date.today()


@app.post("/move")
async def move(body: AITurnRequest):
    if body.turn_phase == TurnPhase.SETUP:
        print("received setup request", flush=True)
        return choose_setup(body.board)
    else:
        jogada = choose_turn(body.board, int(body.your_team))
        print("received turn request", flush=True)
        print(jogada, flush=True)
        return jogada
