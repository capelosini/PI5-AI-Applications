from torch import cuda, device, nn

# check gpu
device = device("cuda" if cuda.is_available() else "cpu")
print("Using ", device)


class Model(nn.Module):
    def __init__(self, tableSize, actionsN):
        super(Model, self).__init__()
        self.conv1 = nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1)
        self.conv2 = nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1)
        self.fc1 = nn.Linear(128 * tableSize * tableSize, actionsN)
        self.relu = nn.ReLU()
        self.softmax = nn.Softmax(dim=1)

    def forward(self, x):
        x = self.relu(self.conv1(x))
        x = self.relu(self.conv2(x))
        x = x.view(x.size(0), -1)
        x = self.softmax(self.fc1(x))
        return x
