# CAPTCHA 2.0 - AI Strategy Game

A distributed AI strategy game project featuring a React-based frontend, a FastAPI-powered AI service, and a deep learning model for game decision-making.

## Project Structure

The repository is organized into three main components:

- **AI/**: The core logic for the AI player.
  - **AI/**: Contains the PyTorch Dueling DQN model implementation (`model.py`) and training scripts.
  - **API/**: A FastAPI service that exposes the AI's moves via HTTP endpoints.
  - **run.py**: A convenience script to start the AI API and expose it via Ngrok for external game servers.
- **Frontend/**: A modern web interface for spectating and managing matches.
  - Built with **React 19**, **Vite**, and **React Router 7**.
  - Provides a real-time game board visualization and match management tools.
- **Shared Utilities**: Common data models and API wrappers in `Frontend/src/utils`.

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+**
- **Node.js 20+**
- **Ngrok** (for exposing the AI to external game servers)

### 1. Setup the AI Service

1. Navigate to the AI directory:
   ```bash
   cd AI
   ```
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Configure environment variables (create a `.env` file):
   ```env
   GAME_API_URL=https://api.example.com
   BOT_ID=your_bot_id
   BOT_TOKEN=your_bot_token
   ```
4. Start the AI service:
   ```bash
   python run.py
   ```
   *Note: This script automatically starts the FastAPI server and Ngrok, then registers the public URL with the specified `GAME_API_URL`.*

### 2. Setup the Frontend

1. Navigate to the Frontend directory:
   ```bash
   cd Frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```
4. Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 🧠 AI Strategy: Dueling DQN Workflow

The CAPTCHA 2.0 AI utilizes a **Dueling Deep Q-Network (DQN)** architecture that learns to play through millions of self-play simulations. Its training and prediction cycle is divided into four distinct phases:

### Phase 1: The Setup (Pre-Match)
- **Neural Architecture**: The system initializes three distinct networks:
    - **Policy Net**: The "Active Brain" that makes real-time decisions and learns from errors.
    - **Target Net**: A "Delayed Brain" used for stable future score calculations.
    - **Opponent Net**: A "Zombie Brain" loaded with historical versions of Turing to provide diverse practice scenarios.
- **Matchmaking**: For every training episode, Turing is matched against either a random bot (to punish simple errors), a past version of itself, or its current self to push strategic boundaries.

### Phase 2: The Action Loop (Gameplay)
The game alternates turns on a 5x5 board:
- **Observation**: The board is converted into a **3-layer state tensor** representing board levels, Turing's pieces, and the enemy's pieces.
- **Decision Making**:
    - **Turing's Turn**: Uses an **Epsilon-Greedy** strategy. Early on, it explores randomly; as it learns, it increasingly relies on the Policy Net for the "smartest" move.
    - **Lovelace's Turn**: Plays based on the opponent type selected in Phase 1.
- **Experience Replay**: Every move Turing makes (State, Action, Reward, Next State) is saved into a **Memory Buffer**. Moves made by Lovelace are ignored to ensure Turing only learns from its own successes and failures.

### Phase 3: The Learning Loop (Training)
Immediately after each move, Turing pauses to "study":
- **Batch Sampling**: 64 random moves are pulled from the Memory Buffer to break temporal correlation.
- **Negamax Calculation**: The AI calculates the "True Value" of a move using the formula:  
  `Expected Q = Reward - (Gamma * Enemy's Future Score)`  
  This forces the AI to realize that setting up an opponent for a win is mathematically catastrophic.
- **Backpropagation**: The Policy Net's weights are tweaked using **Huber Loss** to minimize the difference between its guess and the calculated True Value.

### Phase 4: Evolution (Post-Match)
- **Stats Tracking**: Updates the rolling win rate.
- **Epsilon Decay**: Randomness is gradually reduced, forcing the AI to exploit its mathematical instinct.
- **Brain Sync**: Every 10 games, the Policy Net's weights are copied to the Target Net.
- **League Checkpoints**: Every 500 games, a checkpoint (`.pth`) is saved to a "League" folder to serve as a future opponent.

## Game Rewards Table

| Category | Event | Reward | Description |
| :--- | :--- | :---: | :--- |
| **Wins** | Victory (Level 4) | `+20.0` | Character reaches the winning level. |
| | Victory (Trap) | `+20.0` | Enemy has no valid moves (stalemate win). |
| | Missed Kill | `-10.0` | Penalty for failing to take an available winning move. |
| **Movement** | Move to Level 3 | `+1.5` | Reaching the high-threat level. |
| | Move to Level 2 | `+0.3` | Standard progression reward. |
| **Building** | Setup Own Win | `+1.0` | Upgrading to Level 4 while adjacent and on Level 3. |
| | Enemy Ladder (L4) | `-8.0` | Building a Level 4 platform for an adjacent enemy. |
| | Enemy Ladder (L3) | `-2.0` | Building a Level 3 platform for an adjacent enemy. |
| **Threats** | Enemy on L3 | `-0.5` | Penalty for every turn an enemy remains on Level 3. |
| | Base Turn | `-0.05` | Small penalty to encourage efficiency. |
| | Stalled (>40 turns) | `-0.2` | Increased penalty for long, unproductive games. |

---

## 🎮 Game Rules & Components

### 📺 Spectate Mode
The Frontend includes a dedicated **Spectate** route (`/spectate/:gameId`) that features:
- **Real-time Updates**: Visual representation of the 5x5 board and professor positions.
- **Game Info Panel**: Displays current status, turn number, active team, and phase.
- **Winner Announcement**: When a match concludes (Status: `FINISHED`), a specialized banner displays the winning player and team.

### 🧩 Game Components
- **5x5 Board**: Cells with levels 0-4. Level 4 cells are "graduated" and cannot be occupied or further upgraded.
- **Professors**: Each team (Turing vs. Lovelace) controls two professor tokens.
- **Win Condition**: Be the first to move a professor to a Level 3 cell.

---

## 🛠 Tech Stack

- **Frontend**: React, Vite, CSS (Vanilla), React Router.
- **AI Backend**: Python, FastAPI, Uvicorn, Ngrok.
- **Deep Learning**: PyTorch (Dueling DQN).
- **Deployment**: Environment-based configuration, distributed via REST APIs.
