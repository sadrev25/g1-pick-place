import mujoco
import mujoco.viewer
import numpy as np
import time
import os

with open(os.path.expanduser(
    '~/mujoco_menagerie/unitree_g1/scene.xml')) as f:
    xml = f.read()

objects = """
<body name="red_cube" pos="0.65 0.1 0.44">
  <joint type="free"/>
  <geom type="box" size="0.04 0.04 0.04"
        rgba="0.9 0.2 0.2 1" mass="0.3"/>
  <inertial pos="0 0 0" mass="0.3"
            diaginertia="0.001 0.001 0.001"/>
</body>
<body name="table" pos="0.65 0 0.38">
  <geom type="box" size="0.4 0.3 0.02"
        rgba="0.6 0.4 0.2 1" mass="20"/>
  <inertial pos="0 0 0" mass="20"
            diaginertia="1 1 1"/>
</body>
"""
xml = xml.replace('</worldbody>',
                   objects + '</worldbody>')

os.chdir(os.path.expanduser(
    '~/mujoco_menagerie/unitree_g1'))
model = mujoco.MjModel.from_xml_string(xml)
data  = mujoco.MjData(model)
os.chdir(os.path.expanduser('~'))

r_wrist = mujoco.mj_name2id(
    model, mujoco.mjtObj.mjOBJ_BODY,
    'right_wrist_yaw_link')

mujoco.mj_forward(model, data)

print("=== ARM REACH TEST ===")
print(f"Wrist neutral: {data.xpos[r_wrist]}")

print("\n=== MAX REACH TEST ===")
print("Setting all right arm joints to max...")

# Set shoulder fully forward
data.ctrl[22] =  2.5   # shoulder pitch max
data.ctrl[23] = -2.0   # shoulder roll
data.ctrl[25] = -2.0   # elbow max bend
data.ctrl[14] =  0.6   # waist forward

for _ in range(1000):
    mujoco.mj_step(model, data)

mujoco.mj_forward(model, data)
print(f"Max reach wrist: {data.xpos[r_wrist]}")

# Reset
data.ctrl[:] = 0
for _ in range(500):
    mujoco.mj_step(model, data)
mujoco.mj_forward(model, data)
print(f"After reset: {data.xpos[r_wrist]}")

print("\n=== WHAT IS REACHABLE? ===")
print("Testing different shoulder angles...")
for sp in [0.5, 1.0, 1.5, 2.0, 2.5]:
    data.ctrl[:] = 0
    data.ctrl[22] = sp     # shoulder pitch
    data.ctrl[23] = -0.2   # shoulder roll
    data.ctrl[25] = -1.0   # elbow
    for _ in range(500):
        mujoco.mj_step(model, data)
    mujoco.mj_forward(model, data)
    pos = data.xpos[r_wrist]
    print(f"  shoulder={sp:.1f}: "
          f"wrist at x={pos[0]:.3f} "
          f"y={pos[1]:.3f} "
          f"z={pos[2]:.3f}")

print("\n=== OBJECT IS AT ===")
cube_id = mujoco.mj_name2id(
    model, mujoco.mjtObj.mjOBJ_BODY, 'red_cube')
mujoco.mj_forward(model, data)
print(f"red_cube: {data.xpos[cube_id]}")
print("\nDoes any shoulder angle get close to object?")
