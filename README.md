User: "pick the red cube"
↓
Camera captures scene
↓
GPT-4o identifies object
↓
OpenCV pixel → world xyz
↓
Wrist rotates down (palm facing table)
↓
DLS IK moves arm to position
↓
Behavioral Cloning policy controls joints
↓
Residual PPO corrects errors
↓
Pick + Place ✅

## What's Built

### Vision Pipeline
- GPT-4o object identification
- OpenCV HSV color segmentation
- Camera matrix unprojection to 3D world coordinates

### Control
- Damped Least Squares Jacobian IK (singularity-free)
- Wrist orientation control (palm-down before grasp)
- 7-DOF right arm control for Unitree G1

### Imitation Learning
- Collected 100 expert demonstrations from IK controller
- Trained BCPolicy in PyTorch from scratch
- 100% success rate matching expert performance
- Loss: 0.000002

### Residual RL
- Custom Gymnasium environment
- PPO trained on top of base policy
- 20/20 success rate with ±4cm generalization
- BC base + PPO residual = ResMimic architecture

## Results
| Method | Success Rate | Notes |
|--------|-------------|-------|
| Pure IK | 20/20 | Scripted baseline |
| Residual PPO | 20/20 | RL on top of IK |
| BC Policy | 20/20 | Learned from 100 demos |
| BC + PPO | 20/20 | True ResMimic architecture |
https://youtube.com/shorts/keOu3wBcf0U?is=x48hLS0Ks8czAh0o
