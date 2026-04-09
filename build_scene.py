import mujoco
import mujoco.viewer
import numpy as np
import time
import os
import re

def build_scene():
    g1_dir = os.path.expanduser(
        '~/mujoco_menagerie/unitree_g1')

    with open(f'{g1_dir}/scene.xml') as f:
        scene = f.read()

    with open(f'{g1_dir}/g1.xml') as f:
        g1 = f.read()

    leg_joints = [
        'left_hip_pitch_joint',
        'left_hip_roll_joint',
        'left_hip_yaw_joint',
        'left_knee_joint',
        'left_ankle_pitch_joint',
        'left_ankle_roll_joint',
        'right_hip_pitch_joint',
        'right_hip_roll_joint',
        'right_hip_yaw_joint',
        'right_knee_joint',
        'right_ankle_pitch_joint',
        'right_ankle_roll_joint',
    ]

    # Fix 1 — Remove freejoint
    g1 = g1.replace(
        '<freejoint name="floating_base_joint"/>',
        '')

    # Fix 2 — Remove leg joints
    for jname in leg_joints:
        g1 = re.sub(
            r'<joint name="' + jname + r'"[^/]*/>',
            '', g1)

    # Fix 3 — Remove leg actuators
    for jname in leg_joints:
        g1 = re.sub(
            r'<position[^>]*joint="' +
            jname + r'"[^/]*/>',
            '', g1)

    # Fix 4 — Remove keyframe
    # Keyframe has wrong size after removing joints
    g1 = re.sub(
        r'<keyframe>.*?</keyframe>',
        '', g1, flags=re.DOTALL)

    # Also remove from scene
    scene = re.sub(
        r'<keyframe>.*?</keyframe>',
        '', scene, flags=re.DOTALL)

    # Save fixed g1
    g1_dir_path = g1_dir
    tmp = f'{g1_dir_path}/g1_fixed.xml'
    with open(tmp, 'w') as f:
        f.write(g1)

    # Update scene
    scene = scene.replace(
        '<include file="g1.xml"/>',
        '<include file="g1_fixed.xml"/>')

    # Add objects
    objects = """
    <body name="table" pos="0.65 0 0.38">
      <geom type="box" size="0.4 0.3 0.02"
            rgba="0.6 0.4 0.2 1" mass="20"/>
      <inertial pos="0 0 0" mass="20"
                diaginertia="1 1 1"/>
    </body>
    <body name="red_cube"
          pos="0.60 -0.15 0.44">
      <joint type="free"/>
      <geom type="box" size="0.04 0.04 0.04"
            rgba="0.9 0.2 0.2 1" mass="0.3"/>
      <inertial pos="0 0 0" mass="0.3"
                diaginertia="0.001 0.001 0.001"/>
    </body>
    <body name="blue_cube"
          pos="0.60 0.15 0.43">
      <joint type="free"/>
      <geom type="box"
            size="0.025 0.025 0.025"
            rgba="0.2 0.2 0.9 1" mass="0.1"/>
      <inertial pos="0 0 0" mass="0.1"
          diaginertia="0.0005 0.0005 0.0005"/>
    </body>
    <body name="green_cylinder"
          pos="0.65 -0.05 0.46">
      <joint type="free"/>
      <geom type="cylinder" size="0.03 0.05"
            rgba="0.2 0.8 0.2 1" mass="0.2"/>
      <inertial pos="0 0 0" mass="0.2"
                diaginertia="0.001 0.001 0.001"/>
    </body>
    <body name="container"
          pos="0.55 -0.30 0.01">
      <geom type="box" size="0.15 0.15 0.02"
            rgba="0.3 0.3 0.3 1" mass="5"/>
      <inertial pos="0 0 0" mass="5"
                diaginertia="1 1 1"/>
    </body>
    """
    scene = scene.replace(
        '</worldbody>',
        objects + '</worldbody>')

    return scene, g1_dir

# Build
scene_xml, g1_dir = build_scene()
os.chdir(g1_dir)

try:
    model = mujoco.MjModel.from_xml_string(scene_xml)
    data  = mujoco.MjData(model)
    print(f"✅ Built!")
    print(f"   nv={model.nv}  nu={model.nu}")
except Exception as e:
    print(f"❌ Error: {e}")
    os.chdir(os.path.expanduser('~'))
    exit()

os.chdir(os.path.expanduser('~'))

# Print all joints and actuators
print("\nJoints:")
for i in range(model.njnt):
    print(f"  [{i}] {model.joint(i).name}")

print("\nActuators:")
for i in range(model.nu):
    print(f"  [{i}] {model.actuator(i).name}")

print("\nStarting viewer...")
with mujoco.viewer.launch_passive(
        model, data) as viewer:

    # Settle
    for _ in range(300):
        mujoco.mj_step(model, data)
        viewer.sync()
        time.sleep(0.002)

    print("✅ Robot loaded!")
    print("Testing arm movement...")

    # Test with first few actuators
    # We will use correct indices after
    # seeing the actuator list
    for _ in range(1000):
        mujoco.mj_step(model, data)
        viewer.sync()
        time.sleep(0.002)

    while viewer.is_running():
        mujoco.mj_step(model, data)
        viewer.sync()
        time.sleep(0.002)
