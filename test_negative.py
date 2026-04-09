import mujoco
import mujoco.viewer
import numpy as np
import time
import os
import re

g1_dir = os.path.expanduser(
    '~/mujoco_menagerie/unitree_g1')
with open(f'{g1_dir}/scene.xml') as f:
    scene = f.read()
with open(f'{g1_dir}/g1.xml') as f:
    g1 = f.read()

leg_joints = [
    'left_hip_pitch_joint','left_hip_roll_joint',
    'left_hip_yaw_joint','left_knee_joint',
    'left_ankle_pitch_joint','left_ankle_roll_joint',
    'right_hip_pitch_joint','right_hip_roll_joint',
    'right_hip_yaw_joint','right_knee_joint',
    'right_ankle_pitch_joint','right_ankle_roll_joint',
]
g1 = g1.replace(
    '<freejoint name="floating_base_joint"/>','')
for j in leg_joints:
    g1 = re.sub(r'<joint name="'+j+r'"[^/]*/>', '',g1)
    g1 = re.sub(
        r'<position[^>]*joint="'+j+r'"[^/]*/>', '',g1)
g1 = re.sub(r'<keyframe>.*?</keyframe>',
             '', g1, flags=re.DOTALL)
scene = re.sub(r'<keyframe>.*?</keyframe>',
                '', scene, flags=re.DOTALL)
with open(f'{g1_dir}/g1_fixed.xml','w') as f:
    f.write(g1)
scene = scene.replace(
    '<include file="g1.xml"/>',
    '<include file="g1_fixed.xml"/>')

os.chdir(g1_dir)
model = mujoco.MjModel.from_xml_string(scene)
data  = mujoco.MjData(model)
os.chdir(os.path.expanduser('~'))

r_wrist = mujoco.mj_name2id(
    model, mujoco.mjtObj.mjOBJ_BODY,
    'right_wrist_yaw_link')

def get_wrist():
    mujoco.mj_forward(model, data)
    return data.xpos[r_wrist].copy()

def hold(n=400):
    for _ in range(n):
        mujoco.mj_step(model, data)
        if viewer.is_running():
            viewer.sync()
        time.sleep(0.002)

obj = np.array([0.60, -0.15, 0.44])
print(f"Object at: {obj}")

with mujoco.viewer.launch_passive(
        model, data) as viewer:

    hold(200)

    print("\n=== NEGATIVE SHOULDER TEST ===")
    print("shoulder pitch NEGATIVE = forward?")

    for v in [-0.5, -1.0, -1.5, -2.0, -2.5]:
        data.ctrl[:] = 0
        data.ctrl[2]  =  0.4    # waist pitch
        data.ctrl[10] =  v      # shoulder NEGATIVE
        hold(400)
        w = get_wrist()
        g = np.linalg.norm(obj - w)
        print(f"shoulder={v:.1f}: "
              f"x={w[0]:.3f} "
              f"y={w[1]:.3f} "
              f"z={w[2]:.3f}  "
              f"gap={g:.3f}m")

    data.ctrl[:] = 0
    hold(200)

    print("\n=== BEST REACH TEST ===")
    print("waist=0.6 shoulder=-1.5 elbow=-1.5")
    data.ctrl[2]  =  0.6
    data.ctrl[10] = -1.5
    data.ctrl[13] = -1.5
    hold(600)
    w = get_wrist()
    g = np.linalg.norm(obj - w)
    print(f"Wrist: {w}")
    print(f"Gap:   {g:.3f}m")
    print(f"Object:{obj}")

    data.ctrl[:] = 0
    hold(200)

    print("\n=== FULL REACH SWEEP ===")
    print("Finding best combination...")
    best_gap   = 999
    best_combo = (0,0,0)

    for ws in [0.4, 0.6, 0.8]:
        for sh in [-0.5,-1.0,-1.5,-2.0]:
            for el in [-0.5,-1.0,-1.5,-2.0]:
                data.ctrl[:] = 0
                data.ctrl[2]  = ws
                data.ctrl[10] = sh
                data.ctrl[13] = el
                for _ in range(300):
                    mujoco.mj_step(model,data)
                w = get_wrist()
                g = np.linalg.norm(obj - w)
                if g < best_gap:
                    best_gap   = g
                    best_combo = (ws, sh, el)

    print(f"\nBest combo found:")
    print(f"  waist={best_combo[0]}")
    print(f"  shoulder={best_combo[1]}")
    print(f"  elbow={best_combo[2]}")
    print(f"  gap={best_gap:.3f}m")

    # Show best combo
    data.ctrl[:] = 0
    data.ctrl[2]  = best_combo[0]
    data.ctrl[10] = best_combo[1]
    data.ctrl[13] = best_combo[2]
    hold(600)
    w = get_wrist()
    print(f"\nFinal wrist: {w}")
    print(f"Final gap:   "
          f"{np.linalg.norm(obj-w):.3f}m")

    while viewer.is_running():
        mujoco.mj_step(model, data)
        viewer.sync()
        time.sleep(0.002)
