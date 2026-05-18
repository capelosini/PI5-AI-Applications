# app/scripts/train.py
import glob
import os
import random
import numpy as np
from collections import deque

import torch
import torch.nn.functional as F
import torch.optim as optim

from app.core.constants import ACTIONS_COMBINED, BOARD_SIZE, TEAM_ID, TEAMS
from app.core.game import Game
from app.core.model import Model, device

# --- HYPERPARAMETERS ---
LR = 0.0003
GAMMA = 0.99
BATCH_SIZE = 64
MEMORY_SIZE = 20000
EPSILON_START = 1.0
EPSILON_END = 0.10
EPSILON_DECAY = 0.998
TARGET_UPDATE_FREQ = 10
CHECKPOINT_DIR = "checkpoints"
SAVE_CHECKPOINT_FREQ = 500
MAX_EPISODES = 5000

# --- PER HYPERPARAMETERS ---
PROB_ALPHA = 0.6
BETA_START = 0.4

class PrioritizedReplayBuffer:
    """A simple Prioritized Experience Replay buffer using PyTorch Tensors for fast probability sampling."""
    def __init__(self, capacity, prob_alpha=0.6):
        self.prob_alpha = prob_alpha
        self.capacity = capacity
        self.buffer = []
        self.pos = 0
        self.priorities = torch.zeros(capacity, dtype=torch.float32)

    def push(self, state, action, reward, next_state, done, next_mask):
        max_prio = self.priorities.max() if self.buffer else 1.0

        if len(self.buffer) < self.capacity:
            self.buffer.append((state, action, reward, next_state, done, next_mask))
        else:
            self.buffer[self.pos] = (state, action, reward, next_state, done, next_mask)

        self.priorities[self.pos] = float(max_prio)
        self.pos = (self.pos + 1) % self.capacity

    def sample(self, batch_size, beta=0.4):
        if len(self.buffer) == self.capacity:
            prios = self.priorities
        else:
            prios = self.priorities[:self.pos]

        probs = prios ** self.prob_alpha
        probs /= probs.sum()

        indices = torch.multinomial(probs, batch_size, replacement=True)
        samples = [self.buffer[idx] for idx in indices]

        total = len(self.buffer)
        weights = (total * probs[indices]) ** (-beta)
        weights /= weights.max()

        return samples, indices.tolist(), weights.to(device)

    def update_priorities(self, batch_indices, batch_priorities):
        for idx, prio in zip(batch_indices, batch_priorities):
            self.priorities[idx] = float(prio)

    def __len__(self):
        return len(self.buffer)

# --- GLOBAL OBJECTS ---
policy_net = Model(board_size=BOARD_SIZE, actions_n=128).to(device)
target_net = Model(board_size=BOARD_SIZE, actions_n=128).to(device)
opponent_net = Model(board_size=BOARD_SIZE, actions_n=128).to(device)
target_net.load_state_dict(policy_net.state_dict())

optimizer = optim.Adam(policy_net.parameters(), lr=LR)
# Replace standard deque with our new Prioritized Buffer
memory = PrioritizedReplayBuffer(MEMORY_SIZE, prob_alpha=PROB_ALPHA)
epsilon = EPSILON_START


def get_random_checkpoint():
    checkpoints = glob.glob(os.path.join(CHECKPOINT_DIR, "*.pth"))
    if not checkpoints:
        return None
    return random.choice(checkpoints)


def get_action(net, state, mask, eps=0.0):
    valid_indices = torch.where(mask)[0]
    if random.random() < eps:
        return random.choice(valid_indices.tolist())
    else:
        with torch.no_grad():
            q_values = net(state.unsqueeze(0).to(device))
            q_values[0][~mask] = -1e9
            return torch.argmax(q_values).item()


def optimize_model(beta):
    """Realiza o passo de otimização com Double DQN e Prioritized Experience Replay (PER)."""
    if len(memory) < BATCH_SIZE:
        return

    # 1. Sample Batch (Now includes PER weights and indices)
    batch, indices, weights = memory.sample(BATCH_SIZE, beta)
    states, actions, rewards, next_states, dones, next_masks = zip(*batch)

    state_batch = torch.stack(states).to(device)
    action_batch = torch.tensor(actions).to(device)
    reward_batch = torch.tensor(rewards).to(device)
    next_state_batch = torch.stack(next_states).to(device)
    done_batch = torch.tensor(dones, dtype=torch.float32).to(device)
    next_mask_batch = torch.stack(next_masks).to(device)

    # 2. Get current Q-values
    current_q = policy_net(state_batch).gather(1, action_batch.unsqueeze(1))

    # 3. Get expected Q-values (Adversarial/Zero-Sum with Double DQN)
    with torch.no_grad():
        policy_next_q_values = policy_net(next_state_batch)
        policy_next_q_values[~next_mask_batch] = -1e9
        best_enemy_actions = policy_next_q_values.argmax(dim=1, keepdim=True)

        target_next_q_values = target_net(next_state_batch)
        max_next_q = target_next_q_values.gather(1, best_enemy_actions).squeeze(1)

        expected_q = reward_batch - (GAMMA * max_next_q * (1 - done_batch))

    # 4. Loss calculation with reduction='none' to get individual errors for PER
    loss = F.smooth_l1_loss(current_q.squeeze(), expected_q, reduction='none')
    
    # 5. Update priorities in the buffer (td_error + small constant)
    td_errors = loss.detach().cpu().numpy()
    new_priorities = np.abs(td_errors) + 1e-5
    memory.update_priorities(indices, new_priorities)

    # 6. Apply Importance Sampling weights and take the mean for the final loss
    weighted_loss = (loss * weights).mean()

    optimizer.zero_grad()
    weighted_loss.backward()

    # Gradient clipping
    torch.nn.utils.clip_grad_norm_(policy_net.parameters(), 1.0)
    optimizer.step()


def train():
    global epsilon
    env = Game()
    win_history = deque(maxlen=100)

    print(
        f"[*] Starting Training (PER + Double DQN). Max Episodes: {MAX_EPISODES}"
    )
    print(f"[*] Device: {device} | Index: 0-based | Strategy: Zero-Sum")

    for episode in range(1, MAX_EPISODES + 1):
        env.start()

        # Calculate beta: increases from BETA_START to 1.0 over MAX_EPISODES
        beta = BETA_START + episode * (1.0 - BETA_START) / MAX_EPISODES

        # Seleção de Oponente
        roll = random.random()
        mode = "SELF"
        if roll < 0.20:
            mode = "RANDOM"
        elif roll < 0.50:
            ckpt = get_random_checkpoint()
            if ckpt:
                opponent_net.load_state_dict(torch.load(ckpt, map_location=device))
                mode = f"PAST"
            else:
                mode = "SELF"

        if mode == "SELF":
            opponent_net.load_state_dict(policy_net.state_dict())

        state = env.get_state_tensor()
        total_reward = 0

        while env.status == "PLAYING":
            mask = env.get_valid_mask()
            current_team = TEAM_ID[env.turn_team_id]

            # Escolha de Ação
            if current_team == "turing":
                action = get_action(policy_net, state, mask, epsilon)
            else:
                if mode == "RANDOM":
                    action = random.choice(torch.where(mask)[0].tolist())
                elif mode == "PAST":
                    action = get_action(opponent_net, state, mask, eps=0.05)
                else:  # SELF-PLAY
                    action = get_action(policy_net, state, mask, epsilon)

            # Execução
            reward = env.apply_action(action)
            next_state = env.get_state_tensor()
            done = env.status == "FINISHED"
            next_mask = env.get_valid_mask()

            # Memória
            if current_team == "turing":
                # Now using our custom PER buffer's push method
                memory.push(state, action, reward, next_state, done, next_mask)
                total_reward += reward
                optimize_model(beta)

            state = next_state

        # Stats & Checkpoints
        win_history.append(1 if env.winner == "turing" else 0)
        epsilon = max(EPSILON_END, epsilon * EPSILON_DECAY)

        if episode % TARGET_UPDATE_FREQ == 0:
            target_net.load_state_dict(policy_net.state_dict())

        if episode % 10 == 0:
            win_rate = (sum(win_history) / len(win_history)) * 100
            print(
                f"Ep {episode:04d} | Mode: {mode:6s} | WinRate: {win_rate:4.1f}% | Rew: {total_reward:5.2f} | Eps: {epsilon:.4f}"
            )

        if episode % SAVE_CHECKPOINT_FREQ == 0:
            torch.save(
                policy_net.state_dict(),
                os.path.join(CHECKPOINT_DIR, f"model_ep_{episode}.pth"),
            )

    torch.save(policy_net.state_dict(), "checkpoints/captcha_2.0_final.pth")
    print("\n--- Training Complete ---")


if __name__ == "__main__":
    if not os.path.exists(CHECKPOINT_DIR):
        os.makedirs(CHECKPOINT_DIR)
    train()
