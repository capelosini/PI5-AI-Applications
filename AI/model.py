from torch import cuda, device, nn

# check gpu
device = device("cuda" if cuda.is_available() else "cpu")
print("Using ", device)


class Model(nn.Module):
    def __init__(self, board_size=5, actions_n=128):
        super(Model, self).__init__()

        # Conv Block 1: Captures local patterns (adjacent levels)
        self.conv_block1 = nn.Sequential(
            nn.Conv2d(3, 64, kernel_size=3, padding=1), nn.BatchNorm2d(64), nn.ReLU()
        )

        # Conv Block 2: Captures wider board relationships
        self.conv_block2 = nn.Sequential(
            nn.Conv2d(64, 128, kernel_size=3, padding=1), nn.BatchNorm2d(128), nn.ReLU()
        )

        # 128 filters * 5 * 5 = 3200
        flattened_size = 128 * board_size * board_size

        self.decision_head = nn.Sequential(
            nn.Linear(flattened_size, 512),
            nn.ReLU(),
            nn.Dropout(
                0.2
            ),  # Prevents the AI from over-relying on specific "lucky" moves
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Linear(256, actions_n),  # Raw Q-values
        )

    def forward(self, x):
        # Input x shape: (Batch, 3, 5, 5)
        x = self.conv_block1(x)
        x = self.conv_block2(x)

        # Flatten
        x = x.view(x.size(0), -1)

        # Output Q-values for all 128 actions
        return self.decision_head(x)
