# G1 Humanoid Pick and Place

Vision-guided manipulation for Unitree G1 in MuJoCo.

## Pipeline
User command → GPT-4o → OpenCV → xyz → IK → Pick+Place

## Stack
- MuJoCo physics
- Unitree G1 29-DOF
- GPT-4o vision
- Damped Least Squares IK
- Python 3.10

## Setup
```bash
pip install mujoco openai opencv-python
export OPENAI_API_KEY="sk-..."
python3 main.py
```
