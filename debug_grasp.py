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

# Add cube with collision
objects = """
<body name="red_cube" pos="0.28 -0.10 0.82">
  <joint type="free"/>
  <geom type="box" size="0.04 0.04 0.04"
        rgba="0.9 0.2 0.2 1" mass="0.3"
        contype="1" conaffinity="1"/>
  <inertial pos="0 0 0" mass="0.3"
            diaginertia="0.001 0.001 0.001"/>
</body>
<body name="table" pos="0.28 -0.10 0.75">
  <geom type="box" size="0.20 0.20 0.02"
        rgba="0.6 0.4 0.2 1" mass="20"
        contype="1" conaffinity="1"/>
  <inertial pos="0 0 0" mass="20"
            diaginertia="1 1 1"/>
</body>
"""
scene = scene.replace('</worldbody>',
                       objects + '</worldbody>')

os.chdir(g1_dir)
model = mujoco.MjModel.from_xml_string(scene)
data  = mujoco.MjData(model)
os.chdir(os.path.expanduser('~'))

r_wrist = mujoco.mj_name2id(
    model, mujoco.mjtObj.mjOBJ_BODY,
    'right_wrist_yaw_link')
cube_id = mujoco.mj_name2id(
    model, mujoco.mjtObj.mjOBJ_BODY,
    'red_cube')

def get_wrist():
    mujoco.mj_forward(model, data)
    return data.xpos[r_wrist].copy()

def get_cube():
    mujoco.mj_forward(model, data)
    return data.xpos[cube_id].copy()

def hold(n=200):
    for _ in range(n):
        mujoco.mj_step(model, data)
        if viewer.is_running():
            viewer.sync()
        time.sleep(0.002)

def check_contact():
    for i in range(data.ncon):
        c  = data.contact[i]
        b1 = model.geom_bodyid[c.geom1]
        b2 = model.geom_bodyid[c.geom2]
        if b1 == cube_id or b2 == cube_id:
            return True, c.dist
    return False, 999

print("=== GRASP DEBUG ===")
print("Watch viewer + terminal together")

with mujoco.viewer.launch_passive(
        model, data) as viewer:

    hold(200)
    print(f"Cube:  {get_cube()}")
    print(f"Wrist: {get_wrist()}")

    # Print ALL geoms on wrist and hand
    print("\n=== WRIST/HAND GEOMS ===")
    for g in range(model.ngeom):
        bid = model.geom_bodyid[g]
        bname = model.body(bid).name
        if 'wrist' in bname or 'hand' in bname:
            ct  = model.geom_contype[g]
            ca  = model.geom_conaffinity[g]
            gname = model.geom(g).name
            print(f"  geom[{g}] body={bname:30s} "
                  f"name={gname:20s} "
                  f"contype={ct} conaffinity={ca}")

    print("\n=== CUBE GEOM ===")
    for g in range(model.ngeom):
        bid = model.geom_bodyid[g]
        if bid == cube_id:
            ct  = model.geom_contype[g]
            ca  = model.geom_conaffinity[g]
            print(f"  contype={ct} "
                  f"conaffinity={ca}")

    print("\n=== MOVING ARM TO CUBE ===")
    # Move arm manually to cube
    data.ctrl[10] = -0.3   # shoulder pitch
    data.ctrl[11] = -0.5   # shoulder roll
    data.ctrl[13] = -0.3   # elbow
    hold(500)

    print(f"Wrist: {get_wrist()}")
    print(f"Cube:  {get_cube()}")
    gap = np.linalg.norm(get_wrist()-get_cube())
    print(f"Gap:   {gap:.4f}m")

    contact, dist = check_contact()
    print(f"Contact: {contact} dist={dist:.4f}m")

    print("\n=== PUSHING INTO CUBE ===")
    # Push arm further toward cube
    for step in range(300):
        data.ctrl[10] -= 0.002  # push more
        mujoco.mj_step(model, data)
        viewer.sync()
        time.sleep(0.002)

        contact, dist = check_contact()
        if contact:
            print(f"✅ Contact at step {step}!")
            print(f"   Wrist: {get_wrist()}")
            print(f"   Cube:  {get_cube()}")
            print(f"   Dist:  {dist:.4f}m")
            break
    else:
        print("❌ No contact achieved")
        print(f"   Final gap: "
              f"{np.linalg.norm(get_wrist()-get_cube()):.4f}m")
        print(f"   contype mismatch?")

    while viewer.is_running():
        mujoco.mj_step(model, data)
        viewer.sync()
        time.sleep(0.002)
