import argparse
import csv
import json
import random
from collections import deque
from pathlib import Path

import numpy as np
import torch

from dqn_agent import DQNAgent, DQNConfig, decode_action
from rl_env_stage_22 import GoUpEnv


def parse_args():
    parser = argparse.ArgumentParser(description="Train a DQN agent for GO UP.")
    parser.add_argument("--episodes", type=int, default=1000)
    parser.add_argument("--max-steps", type=int, default=10000)
    parser.add_argument("--eval-interval", type=int, default=25)
    parser.add_argument("--eval-episodes", type=int, default=5)
    parser.add_argument("--checkpoint-interval", type=int, default=50)
    parser.add_argument("--render-every", type=int, default=0)
    parser.add_argument(
        "--output-dir",
        type=str,
        default="training_runs/stage22"
    )
    parser.add_argument("--resume", type=str, default=None)
    parser.add_argument("--seed", type=int, default=42)

    parser.add_argument("--gamma", type=float, default=0.99)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--buffer-size", type=int, default=300000)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--warmup-steps", type=int, default=5000)
    parser.add_argument("--tau", type=float, default=0.005)

    parser.add_argument("--epsilon-start", type=float, default=1.0)
    parser.add_argument("--epsilon-end", type=float, default=0.005)
    parser.add_argument("--epsilon-decay-steps", type=int, default=8000000)

    parser.add_argument("--grad-clip", type=float, default=10.0)
    parser.add_argument("--resume-epsilon", type=float, default=None)

    return parser.parse_args()


def set_global_seed(seed):
    """
    Seed NumPy/PyTorch and the initial Python random state.

    IMPORTANT:
    GoUpEnv.reset(seed=None) intentionally reseeds Python's random
    generator from system randomness for every episode.

    Therefore training/evaluation maps remain fresh and randomized
    instead of following a fixed episode-seed sequence.
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def ensure_output_dir(output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "checkpoints").mkdir(parents=True, exist_ok=True)


def append_csv_row(path, row):
    write_header = not path.exists()

    with path.open("a", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=list(row.keys())
        )

        if write_header:
            writer.writeheader()

        writer.writerow(row)


def run_episode(
    env,
    agent,
    max_steps,
    eval_mode=False,
    seed=None
):
    """
    Run one complete episode.

    seed=None is intentional:
    GoUpEnv.reset(seed=None) generates a completely fresh random map.
    """

    obs = env.reset(seed=seed)

    done = False
    losses = []
    final_info = None

    for step in range(max_steps):

        action_index = agent.select_action(
            obs,
            eval_mode=eval_mode
        )

        next_obs, reward, done, info = env.step(
            decode_action(action_index)
        )

        # ---------------------------------------------------------
        # Training only
        # ---------------------------------------------------------
        if not eval_mode:

            agent.store_transition(
                obs,
                action_index,
                reward,
                next_obs,
                done
            )

            loss = agent.train_step()

            if loss is not None:
                losses.append(loss)

        obs = next_obs
        final_info = info

        if done:
            break

    # -------------------------------------------------------------
    # Safety fallback if episode somehow finishes without info
    # -------------------------------------------------------------
    if final_info is None:

        final_info = env._get_episode_metrics()

        final_info["terminal_reason"] = "max_steps"
        final_info["episode_summary"] = env.get_episode_summary()

    metrics = {
        "episode_reward": final_info["episode_reward"],
        "max_height": final_info["max_height"],
        "unique_platforms": final_info["unique_platforms"],
        "steps_survived": final_info["steps_survived"],
        "terminal_reason": final_info.get("terminal_reason"),
        "loss": (
            float(np.mean(losses))
            if losses
            else float("nan")
        ),
    }

    return metrics


def evaluate(agent, episodes, max_steps):
    """
    Evaluate the current policy on completely fresh random maps.

    Every evaluation episode calls:

        env.reset(seed=None)

    Therefore evaluation does NOT repeatedly test the same
    fixed set of maps.
    """

    eval_env = GoUpEnv(render_mode=None)

    rewards = []
    heights = []
    platform_counts = []
    step_counts = []

    for episode_index in range(episodes):

        metrics = run_episode(
            eval_env,
            agent,
            max_steps=max_steps,
            eval_mode=True,
            seed=None,
        )

        rewards.append(metrics["episode_reward"])
        heights.append(metrics["max_height"])
        platform_counts.append(metrics["unique_platforms"])
        step_counts.append(metrics["steps_survived"])

    eval_env.close()

    return {
        "eval_reward": float(np.mean(rewards)),
        "eval_max_height": float(np.mean(heights)),
        "eval_unique_platforms": float(np.mean(platform_counts)),
        "eval_steps_survived": float(np.mean(step_counts)),
    }


def maybe_render_debug_episode(
    agent,
    max_steps,
    episode_number
):
    """
    Render one completely fresh random map.

    This is evaluation only and does not train the agent.
    """

    render_env = GoUpEnv(render_mode="human")

    metrics = run_episode(
        render_env,
        agent,
        max_steps=max_steps,
        eval_mode=True,
        seed=None,
    )

    render_env.close()

    print(
        f"[render episode {episode_number}] "
        f"reward={metrics['episode_reward']:.2f} "
        f"max_height={metrics['max_height']:.1f} "
        f"unique_platforms={metrics['unique_platforms']} "
        f"steps={metrics['steps_survived']}"
    )


def save_checkpoint(
    agent,
    path,
    episode,
    best_eval_reward
):
    agent.save(
        path,
        extra={
            "episode": episode,
            "best_eval_reward": best_eval_reward,
        },
    )


def main():

    args = parse_args()

    # -------------------------------------------------------------
    # Global reproducibility for NumPy/PyTorch initialization.
    #
    # IMPORTANT:
    # Individual maps are NOT fixed because every env.reset()
    # below uses seed=None.
    # -------------------------------------------------------------
    set_global_seed(args.seed)

    output_dir = Path(args.output_dir)
    ensure_output_dir(output_dir)

    # -------------------------------------------------------------
    # DQN CONFIG
    # -------------------------------------------------------------
    config = DQNConfig(
        gamma=args.gamma,
        lr=args.lr,
        buffer_size=args.buffer_size,
        batch_size=args.batch_size,
        warmup_steps=args.warmup_steps,
        tau=args.tau,
        epsilon_start=args.epsilon_start,
        epsilon_end=args.epsilon_end,
        epsilon_decay_steps=args.epsilon_decay_steps,
        grad_clip=args.grad_clip,
    )

    # -------------------------------------------------------------
    # TRAINING ENVIRONMENT
    # -------------------------------------------------------------
    train_env = GoUpEnv(render_mode=None)

    # This reset is only used to determine observation/action sizes.
    # It also creates one random map, which is harmless.
    initial_obs = train_env.reset(seed=None)

    print(
        f"State dim: {len(initial_obs)}, "
        f"Action dim: {train_env.action_size}"
    )

    agent = DQNAgent(
        state_dim=len(initial_obs),
        action_dim=train_env.action_size,
        config=config,
    )

    # -------------------------------------------------------------
    # SAVE CONFIG
    # -------------------------------------------------------------
    config_path = output_dir / "config.json"

    if not config_path.exists():

        config_payload = vars(args).copy()

        config_payload["observation_size"] = len(initial_obs)
        config_payload["action_size"] = train_env.action_size

        config_path.write_text(
            json.dumps(
                config_payload,
                indent=2
            )
        )

    # -------------------------------------------------------------
    # RESUME STATE
    # -------------------------------------------------------------
    start_episode = 1

    best_eval_reward = float("-inf")
    best_train_reward = float("-inf")

    if args.resume:

        extra = agent.load(args.resume)

        start_episode = (
            int(extra.get("episode", 0)) + 1
        )

        best_eval_reward = float(
            extra.get(
                "best_eval_reward",
                float("-inf")
            )
        )

        print(
            f"Resumed {args.resume} "
            f"at episode {start_episode}"
        )

        if args.resume_epsilon is not None:

            agent.total_steps = int(
                (
                    args.epsilon_start
                    - args.resume_epsilon
                )
                /
                (
                    args.epsilon_start
                    - args.epsilon_end
                )
                *
                args.epsilon_decay_steps
            )

            print(
                f"Epsilon set to "
                f"{agent.epsilon:.2f}"
            )

    # -------------------------------------------------------------
    # METRICS
    # -------------------------------------------------------------
    reward_window = deque(maxlen=50)
    height_window = deque(maxlen=50)

    metrics_csv = (
        output_dir / "episode_metrics.csv"
    )

    checkpoint_dir = (
        output_dir / "checkpoints"
    )

    best_model_path = (
        output_dir / "best_model.pt"
    )

    latest_model_path = (
        output_dir / "latest_model.pt"
    )

    # =============================================================
    # TRAINING LOOP
    # =============================================================
    for episode in range(
        start_episode,
        args.episodes + 1
    ):

        # ---------------------------------------------------------
        # IMPORTANT:
        # A completely NEW RANDOM MAP is generated here.
        #
        # Do NOT replace seed=None with:
        #   args.seed + episode
        #
        # because that would create a deterministic sequence of
        # episode maps.
        # ---------------------------------------------------------
        metrics = run_episode(
            train_env,
            agent,
            max_steps=args.max_steps,
            eval_mode=False,
            seed=None,
        )

        reward_window.append(
            metrics["episode_reward"]
        )

        height_window.append(
            metrics["max_height"]
        )

        moving_avg_reward = float(
            np.mean(reward_window)
        )

        moving_avg_height = float(
            np.mean(height_window)
        )

        epsilon = agent.epsilon
        loss_value = metrics["loss"]

        # ---------------------------------------------------------
        # SAVE TRAINING METRICS
        # ---------------------------------------------------------
        row = {
            "mode": "train",
            "episode": episode,
            "episode_reward": round(
                metrics["episode_reward"],
                4
            ),
            "max_height": round(
                metrics["max_height"],
                4
            ),
            "unique_platforms":
                metrics["unique_platforms"],
            "steps_survived":
                metrics["steps_survived"],
            "moving_avg_reward":
                round(moving_avg_reward, 4),
            "moving_avg_max_height":
                round(moving_avg_height, 4),
            "epsilon":
                round(epsilon, 6),
            "loss": (
                ""
                if (
                    loss_value is None
                    or np.isnan(loss_value)
                )
                else round(loss_value, 6)
            ),
            "terminal_reason":
                metrics["terminal_reason"],
        }

        append_csv_row(
            metrics_csv,
            row
        )

        # ---------------------------------------------------------
        # PRINT TRAINING RESULT
        # ---------------------------------------------------------
        loss_display = (
            "nan"
            if np.isnan(loss_value)
            else f"{loss_value:.4f}"
        )

        print(
            f"[train {episode:05d}] "
            f"reward={metrics['episode_reward']:.2f} "
            f"max_height={metrics['max_height']:.1f} "
            f"unique_platforms={metrics['unique_platforms']} "
            f"steps={metrics['steps_survived']} "
            f"ma_reward={moving_avg_reward:.2f} "
            f"ma_height={moving_avg_height:.1f} "
            f"epsilon={epsilon:.3f} "
            f"loss={loss_display} "
            f"reason={metrics['terminal_reason']}"
        )

        # ---------------------------------------------------------
        # LATEST CHECKPOINT
        # ---------------------------------------------------------
        save_checkpoint(
            agent,
            latest_model_path,
            episode,
            best_eval_reward
        )

        # ---------------------------------------------------------
        # BEST TRAINING MODEL
        # ---------------------------------------------------------
        if (
            metrics["episode_reward"]
            > best_train_reward
        ):

            best_train_reward = (
                metrics["episode_reward"]
            )

            save_checkpoint(
                agent,
                output_dir /
                "best_train_model.pt",
                episode,
                best_train_reward
            )

        # ---------------------------------------------------------
        # PERIODIC CHECKPOINT
        # ---------------------------------------------------------
        if (
            episode
            % args.checkpoint_interval
            == 0
        ):

            save_checkpoint(
                agent,
                checkpoint_dir /
                f"episode_{episode:05d}.pt",
                episode,
                best_eval_reward
            )

        # =========================================================
        # EVALUATION
        # =========================================================
        if (
            args.eval_interval > 0
            and episode % args.eval_interval == 0
        ):

            eval_metrics = evaluate(
                agent,
                episodes=args.eval_episodes,
                max_steps=args.max_steps
            )

            eval_row = {
                "mode": "eval",
                "episode": episode,
                "episode_reward": round(
                    eval_metrics["eval_reward"],
                    4
                ),
                "max_height": round(
                    eval_metrics["eval_max_height"],
                    4
                ),
                "unique_platforms": round(
                    eval_metrics["eval_unique_platforms"],
                    4
                ),
                "steps_survived": round(
                    eval_metrics["eval_steps_survived"],
                    4
                ),
                "moving_avg_reward": "",
                "moving_avg_max_height": "",
                "epsilon": round(
                    agent.epsilon,
                    6
                ),
                "loss": "",
                "terminal_reason": "evaluation",
            }

            append_csv_row(
                metrics_csv,
                eval_row
            )

            print(
                f"[eval  {episode:05d}] "
                f"reward={eval_metrics['eval_reward']:.2f} "
                f"max_height={eval_metrics['eval_max_height']:.1f} "
                f"unique_platforms={eval_metrics['eval_unique_platforms']:.2f} "
                f"steps={eval_metrics['eval_steps_survived']:.1f}"
            )

            # -----------------------------------------------------
            # BEST EVALUATION MODEL
            # -----------------------------------------------------
            if (
                eval_metrics["eval_reward"]
                > best_eval_reward
            ):

                best_eval_reward = (
                    eval_metrics["eval_reward"]
                )

                save_checkpoint(
                    agent,
                    best_model_path,
                    episode,
                    best_eval_reward
                )

                print(
                    f"Saved new best model to "
                    f"{best_model_path}"
                )

        # =========================================================
        # OPTIONAL HUMAN RENDER
        # =========================================================
        if (
            args.render_every > 0
            and episode % args.render_every == 0
        ):

            maybe_render_debug_episode(
                agent,
                max_steps=args.max_steps,
                episode_number=episode
            )

    # -------------------------------------------------------------
    # FALLBACK BEST MODEL
    # -------------------------------------------------------------
    if not best_model_path.exists():

        save_checkpoint(
            agent,
            best_model_path,
            args.episodes,
            best_eval_reward
        )

    train_env.close()


if __name__ == "__main__":
    main()