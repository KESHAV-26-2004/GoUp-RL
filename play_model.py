
import torch
from dqn_agent import DQNAgent
from rl_env_stage_22 import GoUpEnv
from dqn_agent import decode_action

# load env
env = GoUpEnv(render_mode="human")

obs = env.reset()

# load model
agent = DQNAgent(state_dim=len(obs), action_dim=env.action_size)
agent.load("training_runs/model/best_model.pt", load_optimizer=False)

done = False

while not done:
    action = agent.select_action(obs, eval_mode=True)
    obs, reward, done, info = env.step(decode_action(action))

env.close()