import mujoco
import numpy as np
import os, re

G1_DIR = os.path.expanduser("~/mujoco_menagerie/unitree_g1")

with open(f"{G1_DIR}/scene.xml") as f:
    scene = f.read()
with open(f"{G1_DIR}/g1_fixed.xml") as f:
    g1 = f.read()

scene = re.sub(r"<keyframe>.*?</keyframe>", "", scene, flags=re.DOTALL)
scene = scene.replace('<include file="g1.xml"/>', '<include file="g1_fixed.xml"/>')

os.chdir(G1_DIR)
model = mujoco.MjModel.from_xml_string(scene)
data  = mujoco.MjData(model)
os.chdir(os.path.expanduser("~"))

mujoco.mj_forward(model, data)

# Print key body positions
print("=== KEY BODY POSITIONS (neutral pose) ===")
for name in ["pelvis", "torso_link",
             "right_shoulder_pitch_link",
             "right_wrist_yaw_link",
             "left_wrist_yaw_link"]:
    bid = mujoco.mj_name2id(
        model, mujoco.mjtObj.mjOBJ_BODY, name)
    if bid >= 0:
        p = data.xpos[bid]
        print(f"  {name:35s} "
              f"x={p[0]:.3f} y={p[1]:.3f} z={p[2]:.3f}")

# Find all actuator names
print("\n=== ACTUATOR NAMES (arm only) ===")
for i in range(model.nu):
    name = model.actuator(i).name
    if "shoulder" in name or "elbow" in name or "wrist" in name:
        print(f"  [{i}] {name}")

# Quick workspace sample
print("\n=== FINDING BEST REACH POSITION ===")
r_wrist_id = mujoco.mj_name2id(
    model, mujoco.mjtObj.mjOBJ_BODY, "right_wrist_yaw_link")

best_pos  = None
best_x    = -999
all_pos   = []

for c0 in np.linspace(-1.5, 1.5, 8):
    for c1 in np.linspace(-2.5, 0.5, 8):
        for c2 in np.linspace(-2.5, 0.0, 6):
            mujoco.mj_resetData(model, data)
            # Try first 3 arm actuators
            arm_acts = []
            for i in range(model.nu):
                n = model.actuator(i).name
                if any(x in n for x in
                       ["shoulder","elbow"]):
                    arm_acts.append(i)
            for i, aid in enumerate(arm_acts[:3]):
                data.ctrl[aid] = [c0, c1, c2][i]
            for _ in range(150):
                mujoco.mj_step(model, data)
            mujoco.mj_forward(model, data)
            pos = data.xpos[r_wrist_id].copy()
            all_pos.append(pos)
            if pos[0] > best_x and pos[0] > 0.10:
                best_x   = pos[0]
                best_pos = pos.copy()

all_pos = np.array(all_pos)
print(f"  Best forward reach: {best_pos}")
print(f"  Workspace X: {all_pos[:,0].min():.3f} "
      f"to {all_pos[:,0].max():.3f}")
print(f"  Workspace Y: {all_pos[:,1].min():.3f} "
      f"to {all_pos[:,1].max():.3f}")
print(f"  Workspace Z: {all_pos[:,2].min():.3f} "
      f"to {all_pos[:,2].max():.3f}")

# Compute ideal object positions
if best_pos is not None:
    TABLE_Z = best_pos[2] - 0.06
    CUBE_Z  = TABLE_Z + 0.05
    print(f"\n=== USE THESE POSITIONS ===")
    print(f"  table:  {best_pos[0]:.3f} "
          f"{best_pos[1]:.3f} {TABLE_Z:.3f}")
    print(f"  red:    {best_pos[0]:.3f} "
          f"{best_pos[1]:.3f} {CUBE_Z:.3f}")
    print(f"  target: {best_pos[0]-0.10:.3f} "
          f"{best_pos[1]-0.15:.3f} {TABLE_Z:.3f}")
