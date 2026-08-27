# 🎮 GoUp-RL — Deep Reinforcement Learning Platformer Agent

<p align="center">
A Custom Reinforcement Learning Environment Where a DQN Agent Learns to Autonomously Play a Vertical Platformer
</p>

<p align="center">

![Python](https://img.shields.io/badge/Language-Python-blue)
![Pygame](https://img.shields.io/badge/Game-Pygame-green)
![PyTorch](https://img.shields.io/badge/AI-PyTorch-red)
![RL](https://img.shields.io/badge/Method-Deep%20Q--Learning-purple)
![Environment](https://img.shields.io/badge/Environment-Custom%20RL-orange)
![Status](https://img.shields.io/badge/Status-Trained%20Agent-success)

</p>

---

# 📖 Project Overview

**GoUp-RL** is a custom reinforcement learning based platformer game where an AI agent learns to play the game autonomously.

The project combines:

* A complete Pygame based platformer engine
* A custom reinforcement learning environment
* Deep Q-Network (DQN) based agent
* Procedurally generated levels
* Reward engineering
* Automated training and evaluation pipeline

The objective of the agent:

> Learn how to jump across platforms, avoid falling, and reach the highest platform without human input.

The complete game engine, environment, and AI training pipeline are developed from scratch using Python and PyTorch.

---

# 🎮 AI Gameplay Demo

<p align="center">
https://github.com/user-attachments/assets/e3d7c148-16e2-41f9-b8b5-45efd3c75ca5
</p>

The trained agent can autonomously control the player and navigate through randomly generated platform layouts.

---

# 🧠 Reinforcement Learning Architecture

```
          Environment
               |
               |
             State
               |
               v
          DQN Agent
               |
               |
            Action
               |
               v
          Game Physics
               |
               |
      Reward + Next State
               |
               v
       Experience Replay
```

---

# 🤖 Deep Q-Network Agent

The AI agent uses a custom implementation of Deep Q-Learning.

Implemented components:

* Neural network based Q-value prediction
* Experience replay buffer
* Target network updates
* Epsilon-greedy exploration
* Model checkpoint saving
* Evaluation pipeline

The agent learns through:

```
State → Action → Reward → Next State
```

and gradually improves its gameplay strategy.

---

# 🎯 Agent Capabilities

The trained model learns to:

✅ Move left and right
✅ Control jump timing
✅ Select suitable platforms
✅ Avoid falling
✅ Progress vertically
✅ Complete long platform sequences

---

# 🌎 Custom Reinforcement Learning Environment

Unlike standard benchmark environments, GoUp-RL uses a fully custom Pygame environment.

The environment follows a Gym-style design:

```python
reset()
step(action)
close()
```

---

# 👁️ Observation Space

The agent receives information about:

* Player position
* Player velocity
* Jump state
* Nearby platforms
* Platform distance
* Landing candidates
* Movement direction

The observation vector is converted into numerical state information for the neural network.

---

# 🎮 Action Space

The agent controls:

```
Horizontal Movement:
0 → Stay
1 → Move Left
2 → Move Right

Jump:
0 → No Jump
1 → Jump
```

The final action space contains combinations of movement and jumping decisions.

---

# 🌱 Procedural Level Generation

Every episode creates a new random level.

Features:

* Random platform positions
* Random vertical gaps
* Different navigation challenges
* Fresh environment every episode

This prevents the agent from simply memorizing one fixed map.

---

# 🏗️ Environment Stages

Multiple environments were created for progressive learning:

```
rl_env_stage_1.py
rl_env_stage_2.py
rl_env_stage_3.py
rl_env_stage_4.py

rl_env_stage_22.py
rl_env_stage_33.py
```

Different stages introduce:

* Increased platform difficulty
* Longer levels
* More complex navigation

---

# 🏆 Training Results

The latest trained agent demonstrates:

* Successful navigation through large platform sequences
* Learning-based movement decisions
* Generalization across random generated levels
* Completion of extended vertical levels

Training pipeline records:

* Episode reward
* Platforms reached
* Steps survived
* Evaluation performance
* Model checkpoints

---

# 📂 Repository Structure

```
GoUp-RL/

│
├── assets/
│   └── Game resources
│
├── models/
│   └── GoUp_DQN_Model.pt
│
├── demo/
│   └── gameplay.mp4
│
├── dqn_agent.py
│
├── train_dqn.py
│
├── play_model.py
│
├── main.py
│
├── rl_env_stage_1.py
├── rl_env_stage_2.py
├── rl_env_stage_3.py
├── rl_env_stage_4.py
├── rl_env_stage_22.py
├── rl_env_stage_33.py
│
├── requirements.txt
│
└── README.md
```

---

# 🚀 Running The Project

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

# 🎮 Run Normal Game

Start the original playable game:

```bash
python main.py
```

Control the player manually using keyboard controls.

---

# 🤖 Run Trained AI Agent

Run:

```bash
python play_model.py
```

The trained DQN model will automatically control the player.

---

# 🏋️ Train Your Own Agent

Example:

```bash
python train_dqn.py
```

Training supports:

* Random level generation
* Experience replay
* Evaluation episodes
* Model checkpoints
* Reward tracking

---

# 🔬 Technical Highlights

## Artificial Intelligence

* Deep Reinforcement Learning
* DQN Algorithm
* Experience Replay
* Epsilon-Greedy Exploration
* Neural Network Optimization

## Game Development

* Python Pygame Engine
* Physics Simulation
* Collision System
* Procedural Generation

## Software Engineering

* Modular architecture
* Separate training/inference pipeline
* Custom environment design
* Automated evaluation

---

# 🔮 Future Improvements

* CNN based visual agent
* PPO / SAC comparison
* Curriculum learning automation
* Multi-agent training
* Human demonstration learning
* Real-time adaptive difficulty

---

# 👨‍💻 Author

**Keshav**

B.Tech Computer Science Engineering
Bennett University

---

# ⭐ Support

If you like this project, consider giving it a ⭐ on GitHub.
