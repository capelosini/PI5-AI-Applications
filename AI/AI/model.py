from torch import cuda, device, nn

# check gpu
device = device("cuda" if cuda.is_available() else "cpu")
print("Using ", device)


class Model(nn.Module):
    def __init__(self, board_size=5, actions_n=128):
        super(Model, self).__init__()

        # --- FEATURE EXTRACTOR ---
        # Captures local patterns and board-wide relationships
        self.features = nn.Sequential(
            nn.Conv2d(5, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            # Layer 3: Ensures the AI can "see" across the whole 5x5 board
            nn.Conv2d(128, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
        )

        # 128 filters * 5 * 5 = 3200
        flattened_size = 128 * board_size * board_size

        # --- DUELING DQN HEADS ---

        # 1. Value Stream: "How good is the board state overall?"
        self.value_stream = nn.Sequential(
            nn.Linear(flattened_size, 256),
            nn.ReLU(),
            nn.Linear(256, 1),  # Outputs a single number (V)
        )

        # 2. Advantage Stream: "How much better is this specific action?"
        self.advantage_stream = nn.Sequential(
            nn.Linear(flattened_size, 256),
            nn.ReLU(),
            nn.Linear(256, actions_n),  # Outputs 128 numbers (A)
        )

    def forward(self, x):
        # 1. Extract visual features
        x = self.features(x)

        # 2. Flatten
        x = x.view(x.size(0), -1)

        # 3. Calculate Value and Advantage
        values = self.value_stream(x)
        advantages = self.advantage_stream(x)

        # 4. Combine them using the Dueling Aggregation formula
        # Q(s,a) = V(s) + (A(s,a) - mean(A(s,a)))
        q_values = values + (advantages - advantages.mean(dim=1, keepdim=True))

        return q_values
