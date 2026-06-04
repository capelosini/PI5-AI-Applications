from torch import cuda, device, nn

# check gpu
device = device("cuda" if cuda.is_available() else "cpu")


class Model(nn.Module):
    def __init__(self, board_size=5, actions_n=128):
        super(Model, self).__init__()

        # --- FEATURE EXTRACTOR ---
        self.features = nn.Sequential(
            nn.Conv2d(5, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.Conv2d(128, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
        )

        flattened_size = 128 * board_size * board_size

        # --- DUELING DQN HEADS ---
        self.value_stream = nn.Sequential(
            nn.Linear(flattened_size, 256),
            nn.ReLU(),
            nn.Linear(256, 1),
        )

        self.advantage_stream = nn.Sequential(
            nn.Linear(flattened_size, 256),
            nn.ReLU(),
            nn.Linear(256, actions_n),
        )

    def forward(self, x):
        x = self.features(x)
        x = x.view(x.size(0), -1)
        values = self.value_stream(x)
        advantages = self.advantage_stream(x)
        q_values = values + (advantages - advantages.mean(dim=1, keepdim=True))
        return q_values
