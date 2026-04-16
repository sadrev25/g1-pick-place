"""
Train Behavioral Cloning policy.
Run: python3 train_bc.py
"""
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import (
    Dataset, DataLoader)
import numpy as np
import pickle

# ── Dataset ───────────────────────
class DemoDataset(Dataset):
    def __init__(self, demos):
        states  = []
        actions = []
        for demo in demos:
            states.extend(
                demo["states"].tolist())
            actions.extend(
                demo["actions"].tolist())
        self.states  = torch.FloatTensor(
            np.array(states))
        self.actions = torch.FloatTensor(
            np.array(actions))
        print(f"Dataset:")
        print(f"  Transitions: {len(self.states)}")
        print(f"  State dim:   {self.states.shape[1]}")
        print(f"  Action dim:  {self.actions.shape[1]}")

    def __len__(self):
        return len(self.states)

    def __getitem__(self, idx):
        return (self.states[idx],
                self.actions[idx])

# ── Policy Network ────────────────
class BCPolicy(nn.Module):
    def __init__(self, obs_dim=16,
                 act_dim=7,
                 hidden=256):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(obs_dim, hidden),
            nn.LayerNorm(hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden),
            nn.LayerNorm(hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden//2),
            nn.ReLU(),
            nn.Linear(hidden//2, act_dim))

    def forward(self, obs):
        return self.net(obs)

# ── Training ──────────────────────
def train():
    # Load demos
    with open("demos.pkl", "rb") as f:
        demos = pickle.load(f)

    dataset    = DemoDataset(demos)
    dataloader = DataLoader(
        dataset,
        batch_size=256,
        shuffle=True)

    obs_dim = dataset.states.shape[1]
    act_dim = dataset.actions.shape[1]

    policy = BCPolicy(obs_dim, act_dim)
    opt    = optim.Adam(
        policy.parameters(), lr=1e-3)
    sched  = optim.lr_scheduler\
        .CosineAnnealingLR(
            opt, T_max=200)

    print(f"\nTraining BC policy...")
    print(f"Epochs: 200")

    best_loss = float('inf')

    for epoch in range(200):
        epoch_loss = 0
        n_batches  = 0

        for states, actions in dataloader:
            pred = policy(states)
            loss = nn.MSELoss()(
                pred, actions)

            opt.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(
                policy.parameters(), 1.0)
            opt.step()

            epoch_loss += loss.item()
            n_batches  += 1

        sched.step()
        avg = epoch_loss / n_batches

        if avg < best_loss:
            best_loss = avg
            torch.save({
                "model":   policy.state_dict(),
                "obs_dim": obs_dim,
                "act_dim": act_dim,
                "loss":    best_loss,
            }, "bc_policy.pt")

        if epoch % 20 == 0:
            print(f"Epoch {epoch:3d}: "
                  f"loss={avg:.6f} "
                  f"best={best_loss:.6f}")

    print(f"\nBest loss: {best_loss:.6f}")
    print(f"Saved: bc_policy.pt")
    print(f"Next: python3 test_bc.py")

if __name__ == "__main__":
    train()
