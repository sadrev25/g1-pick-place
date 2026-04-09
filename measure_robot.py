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

mujoco.mj_forward(model, data)

print("=== ROBOT BODY POSITIONS (neutral) ===")
important = [
    'pelvis',
    'torso_link',
    'right_shoulder_pitch_link',
    'right_elbow_link',
    'right_wrist_yaw_link',
    'left_wrist_yaw_link',
]
for name in important:
    bid = mujoco.mj_name2id(
        model, mujoco.mjtObj.mjOBJ_BODY, name)
    if bid >= 0:
        pos = data.xpos[bid]
        print(f"  {name:35s} "
              f"x={pos[0]:.3f} "
              f"y={pos[1]:.3f} "
              f"z={pos[2]:.3f}")

print("\n=== WRIST WORKSPACE ===")
r_wrist = mujoco.mj_name2id(
    model, mujoco.mjtObj.mjOBJ_BODY,
    'right_wrist_yaw_link')

positions = []
for c10 in np.linspace(-1.5, 1.5, 8):
    for c11 in np.linspace(-2.5, 0.5, 8):
        for c13 in np.linspace(-2.5, 0.0, 6):
            data.ctrl[10] = c10
            data.ctrl[11] = c11
            data.ctrl[13] = c13
            for _ in range(80):
                mujoco.mj_step(model, data)
            mujoco.mj_forward(model, data)
            positions.append(
                data.xpos[r_wrist].copy())

positions = np.array(positions)
print(f"  X: {positions[:,0].min():.3f} "
      f"to {positions[:,0].max():.3f}")
print(f"  Y: {positions[:,1].min():.3f} "
      f"to {positions[:,1].max():.3f}")
print(f"  Z: {positions[:,2].min():.3f} "
      f"to {positions[:,2].max():.3f}")

# Find densest reachable region
# Where most positions cluster
x_mid = np.median(positions[:,0])
y_mid = np.median(positions[:,1])
z_mid = np.median(positions[:,2])
print(f"\n  Median reach point:")
print(f"  x={x_mid:.3f} y={y_mid:.3f} "
      f"z={z_mid:.3f}")

print("\n=== RECOMMENDED SCENE SETUP ===")
# Table just in front of robot
# at comfortable arm height
table_x = x_mid
table_y = y_mid
table_z = z_mid - 0.05  # slightly below median
print(f"  Table center: "
      f"x={table_x:.3f} "
      f"y={table_y:.3f} "
      f"z={table_z:.3f}")
print(f"  Table surface: "
      f"z={table_z+0.01:.3f}")
print(f"  Objects at:   "
      f"z={table_z+0.01+0.04:.3f} "
      f"(cube on surface)")
print(f"\n  Put this in body.py:")
print(f'  table:   pos="{table_x:.2f} '
      f'{table_y:.2f} {table_z:.2f}"')
print(f'  objects: pos="{table_x:.2f} '
      f'{table_y:.2f} {table_z+0.05:.2f}"')
