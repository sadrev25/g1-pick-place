import mujoco
import mujoco.viewer
import numpy as np
import time
import os
import re

# Load scene
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
for jname in leg_joints:
    g1 = re.sub(
        r'<joint name="'+jname+r'"[^/]*/>', '', g1)
    g1 = re.sub(
        r'<position[^>]*joint="'+jname+r'"[^/]*/>', '', g1)
g1 = re.sub(r'<keyframe>.*?</keyframe>','',
             g1, flags=re.DOTALL)
scene = re.sub(r'<keyframe>.*?</keyframe>','',
                scene, flags=re.DOTALL)

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

def hold(n=300):
    for _ in range(n):
        mujoco.mj_step(model, data)
        if viewer.is_running():
            viewer.sync()
        time.sleep(0.002)

# Object position
obj = np.array([0.60, -0.15, 0.44])
print(f"Object at: {obj}")

with mujoco.viewer.launch_passive(
        model, data) as viewer:

    hold(200)
    print(f"\nNeutral wrist: {get_wrist()}")
    print(f"Gap neutral:   "
          f"{np.linalg.norm(obj-get_wrist()):.3f}m")

    # Test each ctrl one by one
    # Find which ones bring wrist CLOSEST to object
    print("\n=== Testing each joint ===")
    print("Format: ctrl[i] = val → wrist pos → gap")

    best_gap  = 999
    best_combo = {}

    # Test waist pitch (ctrl 2)
    for v in [0.2, 0.4, 0.6, 0.8]:
        data.ctrl[:] = 0
        data.ctrl[2] = v
        hold(300)
        w = get_wrist()
        g = np.linalg.norm(obj - w)
        print(f"waist_pitch={v:.1f}: "
              f"wrist={w}  gap={g:.3f}m")

    data.ctrl[:] = 0
    hold(200)

    # Test shoulder pitch (ctrl 10)
    print()
    for v in [0.5, 1.0, 1.5, 2.0, 2.5]:
        data.ctrl[:] = 0
        data.ctrl[2] =  0.4  # waist
        data.ctrl[10] = v
        hold(300)
        w = get_wrist()
        g = np.linalg.norm(obj - w)
        print(f"shoulder={v:.1f}: "
              f"wrist={w}  gap={g:.3f}m")

    data.ctrl[:] = 0
    hold(200)

    # Test elbow (ctrl 13)
    print()
    for v in [-0.5, -1.0, -1.5, -2.0]:
        data.ctrl[:] = 0
        data.ctrl[2]  =  0.4   # waist
        data.ctrl[10] =  1.5   # shoulder
        data.ctrl[13] =  v     # elbow
        hold(300)
        w = get_wrist()
        g = np.linalg.norm(obj - w)
        print(f"elbow={v:.1f}: "
              f"wrist={w}  gap={g:.3f}m")

    data.ctrl[:] = 0
    hold(200)

    # Best combo test
    print("\n=== Best combo test ===")
    print("Trying waist=0.6 shoulder=2.0 elbow=-1.5")
    data.ctrl[2]  =  0.6
    data.ctrl[10] =  2.0
    data.ctrl[13] = -1.5
    hold(500)
    w = get_wrist()
    g = np.linalg.norm(obj - w)
    print(f"Wrist: {w}")
    print(f"Gap:   {g:.3f}m")

    print("\nHolding — observe in viewer...")
    while viewer.is_running():
        mujoco.mj_step(model, data)
        viewer.sync()
        time.sleep(0.002)
