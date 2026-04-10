"""
Train residual RL policy.
Run: python3 train.py
Watch: tensorboard --logdir logs/
"""
import os
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import (
    check_env)
from stable_baselines3.common.callbacks import (
    EvalCallback,
    CheckpointCallback)
from policy.residual_env import ResidualPickEnv

print("="*45)
print("Residual RL Training")
print("="*45)

# Create dirs
os.makedirs("models/best", exist_ok=True)
os.makedirs("models/checkpoints", exist_ok=True)
os.makedirs("logs", exist_ok=True)

# Setup env
print("\nSetting up environment...")
env = ResidualPickEnv(render=False)

# Validate
print("Validating environment...")
try:
    check_env(env, warn=True)
    print("✅ Environment valid!")
except Exception as e:
    print(f"❌ Fix env: {e}")
    exit()

# Quick sanity check
obs, _ = env.reset()
print(f"\nObs shape: {obs.shape}")
print(f"Obs sample: {obs.round(3)}")
print(f"Action space: {env.action_space}")

# Test 3 random steps
print("\n3 random steps:")
for i in range(3):
    action = env.action_space.sample()
    obs, r, term, trunc, _ = env.step(action)
    print(f"  Step {i+1}: reward={r:.3f} "
          f"done={term or trunc}")

# Callbacks
eval_env = ResidualPickEnv(render=False)
eval_cb  = EvalCallback(
    eval_env,
    best_model_save_path="models/best/",
    log_path            ="logs/eval/",
    eval_freq           =10_000,
    n_eval_episodes     =10,
    deterministic       =True,
    verbose             =1)

ckpt_cb = CheckpointCallback(
    save_freq  =50_000,
    save_path  ="models/checkpoints/",
    name_prefix="residual_pick")

# PPO model
print("\n" + "="*45)
print("Training PPO...")
print("="*45)

model = PPO(
    "MlpPolicy",
    env,
    learning_rate   = 3e-4,
    n_steps         = 2048,
    batch_size      = 64,
    n_epochs        = 10,
    gamma           = 0.99,
    gae_lambda      = 0.95,
    clip_range      = 0.2,
    ent_coef        = 0.01,
    verbose         = 1,
    device          = "cpu",
    tensorboard_log = "logs/")

model.learn(
    total_timesteps = 300_000,
    callback        = [eval_cb, ckpt_cb],
    progress_bar    = True)

# Save final
model.save("models/residual_pick_final")
print("\n✅ Training done!")
print("Saved: models/residual_pick_final")
print("\nRun: python3 test_residual.py")
