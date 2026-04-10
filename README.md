User: "pick the red cube"
↓
Camera captures scene
↓
GPT-4o identifies object → "red cube"
↓
OpenCV finds pixel position → (315, 244)
↓
Camera matrix → world xyz [0.243, -0.174, 0.878]
↓
Damped Least Squares IK → arm moves
↓
Wrist rotates down → palm faces table
↓
Teleport grasp → cube attaches to palm
↓
Lift → Move → Place ✅


# G1 Humanoid Pick and Place
## What's Built
- **Vision**: GPT-4o + OpenCV color detection
  + camera unprojection to 3D world coords
- **Control**: Damped Least Squares IK
  (no singularities, position-only control)
- **Grasp**: Wrist orientation control
  + teleport grasp with palm offset
- **Residual RL**: PPO trained on top of IK
  (20/20 success rate, ±4cm generalization)

## Tech Stack
- MuJoCo 3.x physics simulation
- Unitree G1 29-DOF humanoid
- GPT-4o vision API (object detection)
- OpenCV (color segmentation)
- Stable-Baselines3 PPO
- Python 3.10

## Limitations
- Teleport grasp (not real contact physics)
- Fixed legs (no loco-manipulation yet)
- Single arm pick only
- GPU scarce → MuJoCo instead of Isaac Sim

## Related Paper
ResMimic: From General Motion Tracking to
Humanoid Whole-body Loco-Manipulation
via Residual Learning (Zhao et al. 2025)

## Setup
```bash
pip install mujoco openai opencv-python
pip install stable-baselines3 gymnasium
export OPENAI_API_KEY="sk-..."
python3 main.py
```

## Next Steps
- Real contact grasping (finger joint control)
- Residual RL v2 (joint angle corrections)
- Left arm IK setup
- Loco-manipulation (walking + picking)

```
