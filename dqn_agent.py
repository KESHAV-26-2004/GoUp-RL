from importlib.resources import path
import random
from dataclasses import dataclass

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


HYBRID_ACTIONS = (
    (0, 0),
    (1, 0),
    (2, 0),
    (0, 1),
    (1, 1),
    (2, 1),
)


def decode_action(action_index):
    return HYBRID_ACTIONS[action_index]


def encode_action(horizontal, jump):
    return HYBRID_ACTIONS.index((horizontal, jump))


class ReplayBuffer:
    def __init__(self, capacity, state_dim):
        self.capacity = capacity
        self.state_dim = state_dim
        self.position = 0
        self.size = 0
        self.states = np.zeros((capacity, state_dim), dtype=np.float32)
        self.actions = np.zeros(capacity, dtype=np.int64)
        self.rewards = np.zeros(capacity, dtype=np.float32)
        self.next_states = np.zeros((capacity, state_dim), dtype=np.float32)
        self.dones = np.zeros(capacity, dtype=np.float32)

    def add(self, state, action, reward, next_state, done):
        self.states[self.position] = state
        self.actions[self.position] = action
        self.rewards[self.position] = reward
        self.next_states[self.position] = next_state
        self.dones[self.position] = float(done)

        self.position = (self.position + 1) % self.capacity
        self.size = min(self.size + 1, self.capacity)

    def sample(self, batch_size, device):
        indices = np.random.randint(0, self.size, size=batch_size)
        return {
            "states": torch.as_tensor(self.states[indices], device=device),
            "actions": torch.as_tensor(self.actions[indices], device=device),
            "rewards": torch.as_tensor(self.rewards[indices], device=device),
            "next_states": torch.as_tensor(self.next_states[indices], device=device),
            "dones": torch.as_tensor(self.dones[indices], device=device),
        }

    def __len__(self):
        return self.size


class QNetwork(nn.Module):
    def __init__(self, input_dim, output_dim, hidden_dims=(256, 256)):
        super().__init__()
        layers = []
        prev_dim = input_dim
        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.ReLU())
            prev_dim = hidden_dim
        layers.append(nn.Linear(prev_dim, output_dim))
        self.model = nn.Sequential(*layers)

    def forward(self, x):
        return self.model(x)


@dataclass
class DQNConfig:
    gamma: float = 0.99
    lr: float = 3e-4
    buffer_size: int = 300000
    batch_size: int = 128
    warmup_steps: int = 5000
    tau: float = 0.005
    epsilon_start: float = 1.0
    epsilon_end: float = 0.05
    epsilon_decay_steps: int = 300000
    grad_clip: float = 10.0


class DQNAgent:
    def __init__(self, state_dim, action_dim=6, device=None, config=None):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.config = config or DQNConfig()

        self.online_net = QNetwork(state_dim, action_dim).to(self.device)
        self.target_net = QNetwork(state_dim, action_dim).to(self.device)
        self.target_net.load_state_dict(self.online_net.state_dict())
        self.target_net.eval()

        self.optimizer = torch.optim.Adam(self.online_net.parameters(), lr=self.config.lr)
        self.replay_buffer = ReplayBuffer(self.config.buffer_size, state_dim)

        self.total_steps = 0
        self.learn_steps = 0
        self.last_loss = None

    @property
    def epsilon(self):
        if self.total_steps >= self.config.epsilon_decay_steps:
            return self.config.epsilon_end

        fraction = self.total_steps / max(1, self.config.epsilon_decay_steps)
        return self.config.epsilon_start + fraction * (self.config.epsilon_end - self.config.epsilon_start)

    def select_action(self, state, eval_mode=False):
        state = np.asarray(state, dtype=np.float32)

        if not eval_mode:
            epsilon = self.epsilon
            if self.total_steps < self.config.warmup_steps or random.random() < epsilon:
                action = random.randrange(self.action_dim)
            else:
                action = self._greedy_action(state)
            self.total_steps += 1
            return action

        return self._greedy_action(state)

    def _greedy_action(self, state):
        with torch.no_grad():
            state_tensor = torch.as_tensor(state, dtype=torch.float32, device=self.device).unsqueeze(0)
            q_values = self.online_net(state_tensor)
            return int(torch.argmax(q_values, dim=1).item())

    def store_transition(self, state, action, reward, next_state, done):
        self.replay_buffer.add(
            np.asarray(state, dtype=np.float32),
            int(action),
            float(reward),
            np.asarray(next_state, dtype=np.float32),
            bool(done),
        )

    def train_step(self):
        if self.total_steps < self.config.warmup_steps:
            return None
        if len(self.replay_buffer) < self.config.batch_size:
            return None

        batch = self.replay_buffer.sample(self.config.batch_size, self.device)
        states = batch["states"]
        actions = batch["actions"].unsqueeze(1)
        rewards = batch["rewards"].unsqueeze(1)
        next_states = batch["next_states"]
        dones = batch["dones"].unsqueeze(1)

        q_values = self.online_net(states).gather(1, actions)

        with torch.no_grad():
            next_actions = self.online_net(next_states).argmax(dim=1, keepdim=True)
            next_q_values = self.target_net(next_states).gather(1, next_actions)
            targets = rewards + (1.0 - dones) * self.config.gamma * next_q_values

        loss = F.smooth_l1_loss(q_values, targets)

        self.optimizer.zero_grad(set_to_none=True)
        loss.backward()
        nn.utils.clip_grad_norm_(self.online_net.parameters(), self.config.grad_clip)
        self.optimizer.step()

        self._soft_update_target()
        self.learn_steps += 1
        self.last_loss = float(loss.item())
        return self.last_loss

    def _soft_update_target(self):
        tau = self.config.tau
        for target_param, online_param in zip(self.target_net.parameters(), self.online_net.parameters()):
            target_param.data.mul_(1.0 - tau).add_(tau * online_param.data)

    def save(self, path, extra=None):
        payload = {
            "state_dim": self.state_dim,
            "action_dim": self.action_dim,
            "config": self.config.__dict__,
            "online_net": self.online_net.state_dict(),
            "target_net": self.target_net.state_dict(),
            "optimizer": self.optimizer.state_dict(),
            "total_steps": self.total_steps,
            "learn_steps": self.learn_steps,
            "last_loss": self.last_loss,
            "extra": extra or {},
        }
        torch.save(payload, path)
        # also save lightweight model
        torch.save(self.online_net.state_dict(), str(path).replace(".pt", "_policy.pt"))

    def load(self, path, load_optimizer=True):
        checkpoint = torch.load(path, map_location=self.device)
        self.online_net.load_state_dict(checkpoint["online_net"])
        self.target_net.load_state_dict(checkpoint["target_net"])
        if load_optimizer and "optimizer" in checkpoint:
            self.optimizer.load_state_dict(checkpoint["optimizer"])
        self.total_steps = checkpoint.get("total_steps", 0)
        self.learn_steps = checkpoint.get("learn_steps", 0)
        self.last_loss = checkpoint.get("last_loss")
        return checkpoint.get("extra", {})
