# This script finds EXACT positions
# by simulating robot reaching and measuring

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

r_wrist = mujoco.mj_name2id(
    model, mujoco.mjtObj.mjOBJ_BODY,
    'right_wrist_yaw_link')
pelvis  = mujoco.mj_name2id(
    model, mujoco.mjtObj.mjOBJ_BODY,
    'pelvis')

# Step 1: Find natural reach position
# Set arm to natural reaching pose
data.ctrl[10] = -0.3   # shoulder pitch
data.ctrl[11] = -0.3   # shoulder roll
data.ctrl[13] = -0.3   # elbow

for _ in range(1000):
    mujoco.mj_step(model, data)

mujoco.mj_forward(model, data)
wrist = data.xpos[r_wrist].copy()
pelvis_pos = data.xpos[pelvis].copy()

print(f"Pelvis: {pelvis_pos}")
print(f"Wrist natural reach: {wrist}")
print()

# Step 2: Find where wrist actually is
# Table should be at wrist position
# Objects ON table = wrist height

table_x = wrist[0]
table_y = wrist[1]
table_z = wrist[2] - 0.05  # table just below wrist

# Object positions on table
# All at same x,y as wrist
# z = table surface + object half size

table_surface = table_z + 0.01
red_z    = table_surface + 0.04
blue_z   = table_surface + 0.025
green_z  = table_surface + 0.05

print(f"=== USE THESE POSITIONS ===")
print(f'table:    "{table_x:.2f} {table_y:.2f} {table_z:.2f}"')
print(f'red_cube: "{table_x:.2f} {table_y:.2f} {red_z:.2f}"')
print(f'blue:     "{table_x:.2f} {table_y+0.06:.2f} {blue_z:.2f}"')
print(f'green:    "{table_x:.2f} {table_y-0.06:.2f} {green_z:.2f}"')
print(f'point_B:  "{table_x-0.1:.2f} {table_y-0.15:.2f} {table_z:.2f}"')
print()

# Now write these to body.py
with open('body.py', 'r') as f:
    content = f.read()

# Replace ALL body positions
import re

new_objects = f"""
    <body name="table"
          pos="{table_x:.2f} {table_y:.2f} {table_z:.2f}">
      <geom type="box" size="0.15 0.12 0.01"
            rgba="0.6 0.4 0.2 1" mass="20"
            contype="1" conaffinity="1"/>
      <inertial pos="0 0 0" mass="20"
                diaginertia="1 1 1"/>
    </body>
    <body name="red_cube"
          pos="{table_x:.2f} {table_y:.2f} {red_z:.2f}">
      <joint type="free"/>
      <geom type="box" size="0.04 0.04 0.04"
            rgba="0.9 0.2 0.2 1" mass="0.3"
            contype="1" conaffinity="1"/>
      <inertial pos="0 0 0" mass="0.3"
                diaginertia="0.001 0.001 0.001"/>
    </body>
    <body name="blue_cube"
          pos="{table_x:.2f} {table_y+0.06:.2f} {blue_z:.2f}">
      <joint type="free"/>
      <geom type="box" size="0.025 0.025 0.025"
            rgba="0.2 0.2 0.9 1" mass="0.1"
            contype="1" conaffinity="1"/>
      <inertial pos="0 0 0" mass="0.1"
          diaginertia="0.0005 0.0005 0.0005"/>
    </body>
    <body name="green_cylinder"
          pos="{table_x:.2f} {table_y-0.06:.2f} {green_z:.2f}">
      <joint type="free"/>
      <geom type="cylinder" size="0.03 0.05"
            rgba="0.2 0.8 0.2 1" mass="0.2"
            contype="1" conaffinity="1"/>
      <inertial pos="0 0 0" mass="0.2"
                diaginertia="0.001 0.001 0.001"/>
    </body>
    <body name="container"
          pos="{table_x-0.1:.2f} {table_y-0.15:.2f} {table_z:.2f}">
      <geom type="box" size="0.10 0.10 0.01"
            rgba="0.3 0.3 0.3 1" mass="5"
            contype="1" conaffinity="1"/>
      <inertial pos="0 0 0" mass="5"
                diaginertia="1 1 1"/>
    </body>
"""

# Replace everything between worldbody additions
pattern = r'(<!-- .*?TABLE.*?|<body name="table".*?)(<body name="container".*?</body>)'
full_pattern = r'<body name="table".*?</body>\s*\n\s*<body name="red_cube".*?</body>\s*\n\s*<body name="blue_cube".*?</body>\s*\n\s*<body name="green_cylinder".*?</body>\s*\n\s*<body name="container".*?</body>'

match = re.search(full_pattern, content,
                   re.DOTALL)
if match:
    content = (content[:match.start()] +
               new_objects +
               content[match.end():])
    print("✅ Objects section replaced!")
else:
    print("Pattern not found, manual replace...")
    # Manual replacements
    for old, new in [
        (re.search(r'pos="[\d\. -]+" *(<!--.*?-->)?\s*\n.*?name="table"',
                    content), None),
    ]:
        pass
    print("Please check body.py manually")

with open('body.py', 'w') as f:
    f.write(content)

# Update Point B in main.py
point_b = f"[{table_x-0.1:.2f}, {table_y-0.15:.2f}, {table_z+0.01:.2f}]"
with open('main.py', 'r') as f:
    main = f.read()
main = re.sub(r'POINT_B = \[.*?\]',
               f'POINT_B = {point_b}', main)
with open('main.py', 'w') as f:
    f.write(main)
print(f"✅ Point B = {point_b}")
print("\nDone! Run: python3 main.py")
