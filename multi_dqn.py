import argparse
import csv
import importlib
import json
import random
from collections import deque
from pathlib import Path

import numpy as np
import torch

from dqn_agent import DQNAgent, DQNConfig, decode_action


def parse_args():
    parser = argparse.ArgumentParser(description="Train a DQN agent for GO UP (multi-stage).")
    parser.add_argument("--episodes", type=int, default=1000)
    parser.add_argument("--max-steps", type=int, default=1800)
    parser.add_argument("--eval-interval", type=int, default=25)
    parser.add_argument("--eval-episodes", type=int, default=5)
    parser.add_argument("--checkpoint-interval", type=int, default=50)
    parser.add_argument("--render-every", type=int, default=0)
    parser.add_argument("--output-dir", type=str, default="training_runs/go_up_dqn")
    parser.add_argument("--resume", type=str, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--gamma", type=float, default=0.99)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--buffer-size", type=int, default=300000)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--warmup-steps", type=int, default=5000)
    parser.add_argument("--tau", type=float, default=0.005)
    parser.add_argument("--epsilon-start", type=float, default=1.0)
    parser.add_argument("--epsilon-end", type=float, default=0.05)
    parser.add_argument("--epsilon-decay-steps", type=int, default=1000000)
    parser.add_argument("--grad-clip", type=float, default=10.0)
    parser.add_argument("--resume-epsilon", type=float, default=None)

    # -----------------------------------------------------------------
    # WHICH ENVIRONMENTS TO TRAIN ON
    #
    # Pass any number of module names, each must contain a class
    # named `GoUpEnv` (same contract as your existing stage files).
    #
    # Example:
    #   --stages rl_env_stage_1 rl_env_stage_3 rl_env_stage_4
    #   --stages rl_env_stage_2 rl_env_stage_5
    #
    # This means adding a new stage later (rl_env_stage_5.py, etc.)
    # never requires editing this training script -- just add it to
    # the --stages list on the command line.
    # -----------------------------------------------------------------
    parser.add_argument(
        "--stages",
        type=str,
        nargs="+",
        default=["rl_env_stage_1", "rl_env_stage_2", "rl_env_stage_3"],
        help="Module names to load GoUpEnv from, e.g. rl_env_stage_1 rl_env_stage_3",
    )
    parser.add_argument(
        "--stage-probs",
        type=float,
        nargs="+",
        default=None,
        help=(
            "Sampling probability per stage, in the same order as --stages. "
            "Must match --stages length. Omit for equal probability across "
            "all selected stages."
        ),
    )
    return parser.parse_args()


def load_stage_class(module_name):
    """
    Dynamically import `module_name` and return its GoUpEnv class.
    Raises a clear error if the module or class is missing, instead
    of a confusing traceback deep inside training.
    """
    try:
        module = importlib.import_module(module_name)
    except ImportError as exc:
        raise SystemExit(
            f"Could not import stage module '{module_name}': {exc}\n"
            f"Make sure the file '{module_name}.py' exists and is importable."
        )

    if not hasattr(module, "GoUpEnv"):
        raise SystemExit(
            f"Module '{module_name}' has no class named 'GoUpEnv'. "
            f"Every stage module passed to --stages must define GoUpEnv."
        )

    return module.GoUpEnv


def resolve_stage_probs(stage_names, stage_probs):
    """
    Validate/normalize --stage-probs against --stages.
    Equal probability if not provided; hard error on length mismatch
    rather than silently misaligning names to weights.
    """
    if stage_probs is None:
        n = len(stage_names)
        return [1.0 / n] * n

    if len(stage_probs) != len(stage_names):
        raise SystemExit(
            f"--stage-probs has {len(stage_probs)} values but --stages has "
            f"{len(stage_names)} entries. They must match 1:1, in order:\n"
            f"  stages: {stage_names}\n"
            f"  probs:  {stage_probs}"
        )

    total = sum(stage_probs)
    if total <= 0:
        raise SystemExit("--stage-probs must sum to a positive number.")

    return [p / total for p in stage_probs]


def set_global_seed(seed):
    """
    Seed NumPy/PyTorch and the initial Python random state.

    IMPORTANT:
    Every env.reset() call below uses seed=None, which intentionally
    reseeds Python's random generator from system randomness for
    every single episode. This global seed only controls reproducible
    weight initialization -- it does NOT fix the map sequence.
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
        writer = csv.DictWriter(csv_file, fieldnames=list(row.keys()))
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def build_stage_envs(stage_names, render_mode=None):
    """
    Create ONE persistent instance per selected stage, up front.

    IMPORTANT (pygame lifecycle):
    Each stage class tracks its own _active_envs counter and calls the
    shared, global pygame.quit() once its own counter hits zero. If you
    create-and-close a fresh env every single episode, you end up
    flipping pygame's global state on and off constantly across
    unrelated stage classes, which is both slow and fragile.

    Creating each stage env exactly once and reusing it for the whole
    run -- closing all of them only at the very end -- avoids this
    entirely.
    """
    envs = {}
    for name in stage_names:
        stage_class = load_stage_class(name)
        envs[name] = stage_class(render_mode=render_mode)
    return envs


def validate_stage_compatibility(envs):
    """
    All selected stages share ONE network, so they must produce the
    same observation size and action space. Check this explicitly
    instead of silently letting a mismatched stage corrupt training.
    """
    dims = {}
    for name, env in envs.items():
        obs = env.reset(seed=None)
        dims[name] = (len(obs), env.action_size)

    reference_name = next(iter(dims))
    reference_dims = dims[reference_name]

    mismatched = {
        name: d for name, d in dims.items() if d != reference_dims
    }

    if mismatched:
        details = "\n".join(
            f"  {name}: obs_dim={d[0]}, action_dim={d[1]}" for name, d in dims.items()
        )
        raise SystemExit(
            "Stage observation/action spaces do not match -- a single "
            "network cannot train across incompatible stages:\n"
            f"{details}"
        )

    return reference_dims


def pick_stage_name(stage_names, stage_probs):
    return random.choices(stage_names, weights=stage_probs, k=1)[0]


def run_episode(env, agent, max_steps, eval_mode=False, seed=None):
    """
    Run one complete episode.

    seed=None is intentional: every stage env's reset(seed=None)
    generates a completely fresh random map. Do not pass a
    deterministic seed here for training/eval episodes -- that
    would make the agent see a fixed, repeating map sequence
    instead of learning to generalize.
    """
    obs = env.reset(seed=seed)
    done = False
    losses = []
    final_info = None

    for step in range(max_steps):
        action_index = agent.select_action(obs, eval_mode=eval_mode)
        next_obs, reward, done, info = env.step(decode_action(action_index))

        if not eval_mode:
            agent.store_transition(obs, action_index, reward, next_obs, done)
            loss = agent.train_step()
            if loss is not None:
                losses.append(loss)

        obs = next_obs
        final_info = info
        if done:
            break

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
        "loss": float(np.mean(losses)) if losses else float("nan"),
    }
    return metrics


def evaluate(agent, envs, stage_names, stage_probs, episodes, max_steps):
    """
    Evaluate on a random mix of stages, using the SAME persistent env
    instances passed in (no new pygame inits/quits here). Every
    episode still gets seed=None -> a completely fresh random map,
    matching training conditions.

    NOTE: because stage/map are picked randomly every eval call, the
    resulting eval_reward is noisy from one eval_interval to the next
    -- it's a decent generalization signal but not a precise measure
    of whether the policy improved between two specific checkpoints.
    A fixed-seed benchmark eval is a good addition later if you want
    that precision; not included here yet.
    """
    rewards = []
    heights = []
    platform_counts = []
    step_counts = []

    for _ in range(episodes):
        stage_name = pick_stage_name(stage_names, stage_probs)
        eval_env = envs[stage_name]

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

    return {
        "eval_reward": float(np.mean(rewards)),
        "eval_max_height": float(np.mean(heights)),
        "eval_unique_platforms": float(np.mean(platform_counts)),
        "eval_steps_survived": float(np.mean(step_counts)),
    }


def maybe_render_debug_episode(agent, envs, stage_names, stage_probs, max_steps, episode_number):
    """
    Render one fresh random map on a random stage. Evaluation only,
    does not train the agent. Reuses the persistent env instances.
    """
    stage_name = pick_stage_name(stage_names, stage_probs)
    render_env = envs[stage_name]

    metrics = run_episode(
        render_env,
        agent,
        max_steps=max_steps,
        eval_mode=True,
        seed=None,
    )

    print(
        f"[render episode {episode_number} | stage={stage_name}] "
        f"reward={metrics['episode_reward']:.2f} "
        f"max_height={metrics['max_height']:.1f} "
        f"unique_platforms={metrics['unique_platforms']} "
        f"steps={metrics['steps_survived']}"
    )


def save_checkpoint(agent, path, episode, best_eval_reward, best_train_reward):
    agent.save(
        path,
        extra={
            "episode": episode,
            "best_eval_reward": best_eval_reward,
            "best_train_reward": best_train_reward,
        },
    )


def main():
    args = parse_args()

    # -------------------------------------------------------------
    # Global reproducibility for NumPy/PyTorch initialization only.
    # Individual maps are NOT fixed -- every env.reset() below uses
    # seed=None.
    # -------------------------------------------------------------
    set_global_seed(args.seed)

    stage_names = args.stages
    stage_probs = resolve_stage_probs(stage_names, args.stage_probs)

    print("Training on stages:")
    for name, prob in zip(stage_names, stage_probs):
        print(f"  {name}: {prob:.3f}")

    output_dir = Path(args.output_dir)
    ensure_output_dir(output_dir)

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
    # PERSISTENT MULTI-STAGE ENVIRONMENTS
    # Created ONCE. Reused for every episode (train/eval/render).
    # Closed ONCE at the very end of the script.
    # -------------------------------------------------------------
    envs = build_stage_envs(stage_names, render_mode=None)

    # All selected stages must share one observation/action space
    # since they feed a single shared network. This resets every
    # stage once (harmless) and hard-fails with a clear message if
    # any stage doesn't match the others.
    obs_dim, action_size = validate_stage_compatibility(envs)

    print(f"State dim: {obs_dim}, Action dim: {action_size}")

    agent = DQNAgent(
        state_dim=obs_dim,
        action_dim=action_size,
        config=config,
    )

    # -------------------------------------------------------------
    # SAVE CONFIG
    # -------------------------------------------------------------
    config_path = output_dir / "config.json"
    if not config_path.exists():
        config_payload = vars(args).copy()
        config_payload["observation_size"] = obs_dim
        config_payload["action_size"] = action_size
        config_payload["stages"] = stage_names
        config_payload["stage_probs"] = stage_probs
        config_path.write_text(json.dumps(config_payload, indent=2))

    # -------------------------------------------------------------
    # RESUME STATE
    # -------------------------------------------------------------
    start_episode = 1
    best_eval_reward = float("-inf")
    best_train_reward = float("-inf")

    if args.resume:
        extra = agent.load(args.resume)
        start_episode = int(extra.get("episode", 0)) + 1
        best_eval_reward = float(extra.get("best_eval_reward", float("-inf")))
        # Restore best_train_reward too -- otherwise it silently resets
        # to -inf on every resume and the very next episode gets
        # written out as "best_train_model" even if it's worse than
        # what you already had.
        best_train_reward = float(extra.get("best_train_reward", float("-inf")))

        print(f"Resumed {args.resume} at episode {start_episode}")

        # NOTE: the replay buffer is intentionally NOT saved/restored
        # (kept empty on resume, as requested). The agent will refill
        # it from scratch via warmup_steps before training resumes.
        if args.resume_epsilon is not None:
            agent.total_steps = int(
                (args.epsilon_start - args.resume_epsilon)
                / (args.epsilon_start - args.epsilon_end)
                * args.epsilon_decay_steps
            )
            print(f"Epsilon set to {agent.epsilon:.2f}")

    # -------------------------------------------------------------
    # METRICS
    # -------------------------------------------------------------
    reward_window = deque(maxlen=50)
    height_window = deque(maxlen=50)

    metrics_csv = output_dir / "episode_metrics.csv"
    checkpoint_dir = output_dir / "checkpoints"
    best_model_path = output_dir / "best_model.pt"
    latest_model_path = output_dir / "latest_model.pt"

    # =============================================================
    # TRAINING LOOP
    # =============================================================
    for episode in range(start_episode, args.episodes + 1):

        stage_name = pick_stage_name(stage_names, stage_probs)
        train_env = envs[stage_name]

        # ---------------------------------------------------------
        # IMPORTANT: always seed=None -> a completely NEW RANDOM MAP
        # is generated on the chosen stage every episode. Do NOT
        # replace this with a deterministic seed sequence.
        # ---------------------------------------------------------
        metrics = run_episode(
            train_env,
            agent,
            max_steps=args.max_steps,
            eval_mode=False,
            seed=None,
        )

        reward_window.append(metrics["episode_reward"])
        height_window.append(metrics["max_height"])

        moving_avg_reward = float(np.mean(reward_window))
        moving_avg_height = float(np.mean(height_window))
        epsilon = agent.epsilon
        loss_value = metrics["loss"]

        row = {
            "mode": "train",
            "episode": episode,
            "stage": stage_name,
            "episode_reward": round(metrics["episode_reward"], 4),
            "max_height": round(metrics["max_height"], 4),
            "unique_platforms": metrics["unique_platforms"],
            "steps_survived": metrics["steps_survived"],
            "moving_avg_reward": round(moving_avg_reward, 4),
            "moving_avg_max_height": round(moving_avg_height, 4),
            "epsilon": round(epsilon, 6),
            "loss": "" if (loss_value is None or np.isnan(loss_value)) else round(loss_value, 6),
            "terminal_reason": metrics["terminal_reason"],
        }
        append_csv_row(metrics_csv, row)

        loss_display = "nan" if np.isnan(loss_value) else f"{loss_value:.4f}"

        print(
            f"[train {episode:05d} | {stage_name}] "
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
        save_checkpoint(agent, latest_model_path, episode, best_eval_reward, best_train_reward)

        # ---------------------------------------------------------
        # BEST TRAINING MODEL
        # ---------------------------------------------------------
        if metrics["episode_reward"] > best_train_reward:
            best_train_reward = metrics["episode_reward"]
            save_checkpoint(
                agent, output_dir / "best_train_model.pt", episode, best_eval_reward, best_train_reward
            )

        # ---------------------------------------------------------
        # PERIODIC CHECKPOINT
        # ---------------------------------------------------------
        if episode % args.checkpoint_interval == 0:
            save_checkpoint(
                agent,
                checkpoint_dir / f"episode_{episode:05d}.pt",
                episode,
                best_eval_reward,
                best_train_reward,
            )

        # =========================================================
        # EVALUATION
        # =========================================================
        if args.eval_interval > 0 and episode % args.eval_interval == 0:
            eval_metrics = evaluate(
                agent,
                envs,
                stage_names,
                stage_probs,
                episodes=args.eval_episodes,
                max_steps=args.max_steps,
            )

            eval_row = {
                "mode": "eval",
                "episode": episode,
                "stage": "mixed",
                "episode_reward": round(eval_metrics["eval_reward"], 4),
                "max_height": round(eval_metrics["eval_max_height"], 4),
                "unique_platforms": round(eval_metrics["eval_unique_platforms"], 4),
                "steps_survived": round(eval_metrics["eval_steps_survived"], 4),
                "moving_avg_reward": "",
                "moving_avg_max_height": "",
                "epsilon": round(agent.epsilon, 6),
                "loss": "",
                "terminal_reason": "evaluation",
            }
            append_csv_row(metrics_csv, eval_row)

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
            if eval_metrics["eval_reward"] > best_eval_reward:
                best_eval_reward = eval_metrics["eval_reward"]
                save_checkpoint(agent, best_model_path, episode, best_eval_reward, best_train_reward)
                print(f"Saved new best model to {best_model_path}")

        # =========================================================
        # OPTIONAL HUMAN RENDER
        # =========================================================
        if args.render_every > 0 and episode % args.render_every == 0:
            maybe_render_debug_episode(
                agent,
                envs,
                stage_names,
                stage_probs,
                max_steps=args.max_steps,
                episode_number=episode,
            )

    # -------------------------------------------------------------
    # FALLBACK BEST MODEL
    # -------------------------------------------------------------
    if not best_model_path.exists():
        save_checkpoint(agent, best_model_path, args.episodes, best_eval_reward, best_train_reward)

    # -------------------------------------------------------------
    # CLOSE ALL PERSISTENT ENVS (once, at the very end)
    # -------------------------------------------------------------
    for env in envs.values():
        env.close()


if __name__ == "__main__":
    main()