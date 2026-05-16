import os
import random
from collections import deque

import torch
import torch.nn.functional as F
import torch.optim as optim
from game import BOARD_SIZE, TEAM_ID, Game
from model import Model, device

CHECKPOINT_DIR = "./checkpoints"
SAVE_CHECKPOINT_FREQ = 500
if not os.path.exists(CHECKPOINT_DIR):
    os.makedirs(CHECKPOINT_DIR)

LR = 0.0003  # Lower for Dueling DQN stability
GAMMA = 0.99  # Focus on long-term strategy (Trapping)
BATCH_SIZE = 64
MEMORY_SIZE = 20000  # Larger buffer for diverse opponent experience
EPSILON_START = 1.0
EPSILON_END = 0.10
EPSILON_DECAY = 0.998  # Slower decay for more exploration
TARGET_UPDATE_FREQ = 10

# Initialize Models
policy_net = Model(board_size=BOARD_SIZE, actions_n=128).to(device)
target_net = Model(board_size=BOARD_SIZE, actions_n=128).to(device)
opponent_net = Model(board_size=BOARD_SIZE, actions_n=128).to(device)
target_net.load_state_dict(policy_net.state_dict())

optimizer = optim.Adam(policy_net.parameters(), lr=LR)
memory = deque(maxlen=MEMORY_SIZE)
epsilon = EPSILON_START

# Tracking stats
win_history = deque(maxlen=100)  # Track last 100 games


def select_opponent_mode():
    roll = random.random()
    if roll < 0.20:
        return "RANDOM"
    elif roll < 0.50 and len(os.listdir(CHECKPOINT_DIR)) > 0:
        return "PAST"
    else:
        return "SELF"


def get_action(net, state, mask, eps=0.0):
    valid_indices = torch.where(mask)[0]
    if random.random() < eps:
        return random.choice(valid_indices.tolist())
    else:
        with torch.no_grad():
            q_values = net(state.unsqueeze(0).to(device))
            q_values[0][~mask] = -1e9
            return torch.argmax(q_values).item()


def optimize_model():
    if len(memory) < BATCH_SIZE:
        return

    batch = random.sample(memory, BATCH_SIZE)
    states, actions, rewards, next_states, dones, next_masks = zip(*batch)

    state_batch = torch.stack(states).to(device)
    action_batch = torch.tensor(actions).to(device)
    reward_batch = torch.tensor(rewards).to(device)
    next_state_batch = torch.stack(next_states).to(device)
    done_batch = torch.tensor(dones, dtype=torch.float32).to(device)
    next_mask_batch = torch.stack(next_masks).to(device)

    # 1. Get current Q-values
    current_q = policy_net(state_batch).gather(1, action_batch.unsqueeze(1))

    # 2. Get expected Q-values
    with torch.no_grad():
        next_q_values = target_net(next_state_batch)
        next_q_values[~next_mask_batch] = -1e9

        # This is the ENEMY'S max future score
        max_next_q = next_q_values.max(1)[0]

        # Subtract the enemy's expected Q-value
        expected_q = reward_batch - (GAMMA * max_next_q * (1 - done_batch))

    loss = F.smooth_l1_loss(current_q.squeeze(), expected_q)

    optimizer.zero_grad()
    loss.backward()
    # Gradient clipping: prevents the "exploding gradient" problem
    torch.nn.utils.clip_grad_norm_(policy_net.parameters(), 1.0)
    optimizer.step()


# --- Simulation Loop ---
num_episodes = 2000

for episode in range(num_episodes):
    game = Game()
    game.start()

    mode = select_opponent_mode()
    if mode == "PAST":
        past_models = os.listdir(CHECKPOINT_DIR)
        chosen = random.choice(past_models)
        opponent_net.load_state_dict(torch.load(os.path.join(CHECKPOINT_DIR, chosen)))

    state = game.get_state_tensor()
    total_reward = 0

    while game.status == "PLAYING":
        mask = game.get_valid_mask()
        current_team = TEAM_ID[game.turn_team_id]

        if current_team == "turing":
            action = get_action(policy_net, state, mask, epsilon)
        else:
            if mode == "RANDOM":
                action = random.choice(torch.where(mask)[0].tolist())
            elif mode == "PAST":
                action = get_action(opponent_net, state, mask, eps=0.05)
            else:  # SELF-PLAY
                action = get_action(policy_net, state, mask, epsilon)

        reward = game.apply_action(action)
        next_state = game.get_state_tensor()
        done = game.status == "FINISHED"
        next_mask = game.get_valid_mask()

        if current_team == "turing":
            memory.append((state, action, reward, next_state, done, next_mask))
            total_reward += reward

        state = next_state
        optimize_model()

    # Tracking win rate
    win_history.append(1 if game.winner == "turing" else 0)
    current_win_rate = (sum(win_history) / len(win_history)) * 100

    epsilon = max(EPSILON_END, epsilon * EPSILON_DECAY)

    if episode % TARGET_UPDATE_FREQ == 0:
        target_net.load_state_dict(policy_net.state_dict())

    if episode % SAVE_CHECKPOINT_FREQ == 0:
        torch.save(policy_net.state_dict(), f"{CHECKPOINT_DIR}/model_ep_{episode}.pth")

    print(
        f"Ep {episode:04d} | Mode: {mode:6s} | WinRate: {current_win_rate:4.1f}% | Score: {total_reward:5.2f} | Winner: {game.winner}"
    )

torch.save(policy_net.state_dict(), "captcha_2.0_final.pth")
