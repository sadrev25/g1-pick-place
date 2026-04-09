import mujoco
import numpy as np
import os, re

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
    g1 = re.sub(
        r'<joint name="'+j+r'"[^/]*/>', '', g1)
    g1 = re.sub(
        r'<position[^>]*joint="'+j+r'"[^/]*/>', '', g1)
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

# Find maximum reachable positions
# by trying all joint combinations
print("Finding reachable workspace...")

max_x = -999
max_positions = []

# Sample many joint combinations
np.random.seed(42)
n_samples = 5000

for _ in range(n_samples):
    # Random joint angles within limits
    data.ctrl[2]  = np.random.uniform(-0.5, 0.8)
    data.ctrl[10] = np.random.uniform(-2.5, 1.5)
    data.ctrl[11] = np.random.uniform(-2.5, 0.5)
    data.ctrl[12] = np.random.uniform(-1.5, 1.5)
    data.ctrl[13] = np.random.uniform(-2.5, 0.0)
    data.ctrl[14] = np.random.uniform(-1.5, 1.5)
    data.ctrl[15] = np.random.uniform(-1.0, 1.0)
    data.ctrl[16] = np.random.uniform(-1.5, 1.5)

    for _ in range(50):
        mujoco.mj_step(model, data)

    mujoco.mj_forward(model, data)
    w = data.xpos[r_wrist].copy()
    max_positions.append(w)
    if w[0] > max_x:
        max_x = w[0]

positions = np.array(max_positions)

print(f"\n=== REACHABLE WORKSPACE ===")
print(f"X range: {positions[:,0].min():.3f} "
      f"to {positions[:,0].max():.3f}")
print(f"Y range: {positions[:,1].min():.3f} "
      f"to {positions[:,1].max():.3f}")
print(f"Z range: {positions[:,2].min():.3f} "
      f"to {positions[:,2].max():.3f}")

print(f"\nMax X reach: {positions[:,0].max():.3f}m")
print(f"Current pelvis X: 0.0")

# Find positions reachable near table height
table_height = 0.44
reachable = positions[
    (positions[:,2] > table_height - 0.1) &
    (positions[:,2] < table_height + 0.1)
]

if len(reachable) > 0:
    print(f"\nAt table height z≈{table_height}:")
    print(f"X range: {reachable[:,0].min():.3f} "
          f"to {reachable[:,0].max():.3f}")
    print(f"Y range: {reachable[:,1].min():.3f} "
          f"to {reachable[:,1].max():.3f}")
    print(f"\nSuggested object position:")
    print(f"  x = {reachable[:,0].max()*0.8:.3f} "
          f"(80% of max reach)")
    print(f"  y = -0.15 (right side)")
    print(f"  z = {table_height:.3f}")
