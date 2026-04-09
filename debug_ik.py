import mujoco
import mujoco.viewer
import numpy as np
import time
import os

# Load robot
with open(os.path.expanduser(
    '~/mujoco_menagerie/unitree_g1/scene.xml')) as f:
    xml = f.read()

os.chdir(os.path.expanduser(
    '~/mujoco_menagerie/unitree_g1'))
model = mujoco.MjModel.from_xml_string(xml)
data  = mujoco.MjData(model)
os.chdir(os.path.expanduser('~'))

mujoco.mj_forward(model, data)

# Find wrist ID
r_wrist = mujoco.mj_name2id(
    model, mujoco.mjtObj.mjOBJ_BODY,
    'right_wrist_yaw_link')

print("=== CURRENT WRIST POSITION ===")
print(f"Right wrist: {data.xpos[r_wrist]}")

print("\n=== MODEL DOF INFO ===")
print(f"Total DOF (nv): {model.nv}")
print(f"Total actuators (nu): {model.nu}")

print("\n=== JACOBIAN TEST ===")
jacp = np.zeros((3, model.nv))
jacr = np.zeros((3, model.nv))
mujoco.mj_jac(model, data, jacp, jacr,
               data.xpos[r_wrist], r_wrist)

print("Jacobian non-zero columns:")
for i in range(model.nv):
    col = jacp[:, i]
    if np.linalg.norm(col) > 0.001:
        print(f"  DOF {i}: {col}")

print("\n=== MOVE SHOULDER TEST ===")
print("Setting ctrl[22] = 1.0 (right shoulder pitch)")
data.ctrl[22] = 1.0
for _ in range(500):
    mujoco.mj_step(model, data)
mujoco.mj_forward(model, data)
print(f"Wrist after shoulder move: {data.xpos[r_wrist]}")

data.ctrl[22] = 0.0
for _ in range(500):
    mujoco.mj_step(model, data)
mujoco.mj_forward(model, data)
print(f"Wrist after reset: {data.xpos[r_wrist]}")
