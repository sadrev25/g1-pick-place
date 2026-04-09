import mujoco
import numpy as np
import os, re

G1_DIR = os.path.expanduser("~/mujoco_menagerie/unitree_g1")

with open(f"{G1_DIR}/scene.xml") as f:
    scene = f.read()
with open(f"{G1_DIR}/g1_fixed.xml") as f:
    g1 = f.read()

scene = re.sub(r"<keyframe>.*?</keyframe>",
               "", scene, flags=re.DOTALL)
scene = scene.replace(
    '<include file="g1.xml"/>',
    '<include file="g1_fixed.xml"/>')

os.chdir(G1_DIR)
model = mujoco.MjModel.from_xml_string(scene)
data  = mujoco.MjData(model)
os.chdir(os.path.expanduser("~"))

r_wrist_id = mujoco.mj_name2id(
    model, mujoco.mjtObj.mjOBJ_BODY,
    "right_wrist_yaw_link")

arm_ctrl_ids = []
for name in ["right_shoulder_pitch_joint",
             "right_shoulder_roll_joint",
             "right_elbow_joint"]:
    aid = mujoco.mj_name2id(
        model, mujoco.mjtObj.mjOBJ_ACTUATOR, name)
    if aid >= 0:
        arm_ctrl_ids.append(aid)

print(f"Arm ctrl ids: {arm_ctrl_ids}")

all_pos = []
for c0 in np.linspace(-1.5, 1.5, 8):
    for c1 in np.linspace(-2.5, 0.5, 8):
        for c2 in np.linspace(-2.5, 0.0, 6):
            mujoco.mj_resetData(model, data)
            for i, aid in enumerate(arm_ctrl_ids[:3]):
                data.ctrl[aid] = [c0,c1,c2][i]
            for _ in range(150):
                mujoco.mj_step(model, data)
            mujoco.mj_forward(model, data)
            all_pos.append(
                data.xpos[r_wrist_id].copy())

all_pos = np.array(all_pos)
front   = all_pos[all_pos[:,0] > 0.10]
if len(front) == 0:
    front = all_pos

z_med    = np.median(front[:,2])
natural  = front[np.abs(front[:,2]-z_med) < 0.05]
if len(natural) == 0:
    natural = front

WRIST = natural[np.argmax(natural[:,0])]

TABLE_Z       = WRIST[2] - 0.06
TABLE_SURFACE = TABLE_Z + 0.01
CUBE_Z        = TABLE_SURFACE + 0.04

TABLE  = np.array([WRIST[0],       WRIST[1],       TABLE_Z])
RED    = np.array([WRIST[0],       WRIST[1],       CUBE_Z])
BLUE   = np.array([WRIST[0],       WRIST[1]+0.08,  CUBE_Z])
GREEN  = np.array([WRIST[0],       WRIST[1]-0.08,  CUBE_Z+0.01])
TARGET = np.array([WRIST[0]-0.10,  WRIST[1]-0.15,  TABLE_SURFACE])

print(f"\nWrist best: {WRIST}")
print(f"Table:      {TABLE}")
print(f"Red:        {RED}")
print(f"Blue:       {BLUE}")
print(f"Green:      {GREEN}")
print(f"Target:     {TARGET}")

print("\nReachability:")
for name, pos in [("red",RED),("blue",BLUE),
                  ("green",GREEN),("target",TARGET)]:
    gap = np.linalg.norm(WRIST - pos)
    ok  = "OK" if gap < 0.15 else "OUT OF REACH"
    print(f"  [{ok}] {name}: gap={gap:.3f}m")

# Update body.py
with open("body.py","r") as f:
    content = f.read()

for pattern, replacement in [
    (r'<body name="table"(\s+)pos="[^"]*"',
     f'<body name="table"\\1pos="{TABLE[0]:.3f} {TABLE[1]:.3f} {TABLE[2]:.3f}"'),
    (r'<body name="red_cube"(\s+)pos="[^"]*"',
     f'<body name="red_cube"\\1pos="{RED[0]:.3f} {RED[1]:.3f} {RED[2]:.3f}"'),
    (r'<body name="blue_cube"(\s+)pos="[^"]*"',
     f'<body name="blue_cube"\\1pos="{BLUE[0]:.3f} {BLUE[1]:.3f} {BLUE[2]:.3f}"'),
    (r'<body name="green_cylinder"(\s+)pos="[^"]*"',
     f'<body name="green_cylinder"\\1pos="{GREEN[0]:.3f} {GREEN[1]:.3f} {GREEN[2]:.3f}"'),
    (r'<body name="container"(\s+)pos="[^"]*"',
     f'<body name="container"\\1pos="{TARGET[0]:.3f} {TARGET[1]:.3f} {TARGET[2]:.3f}"'),
]:
    new = re.sub(pattern, replacement, content)
    if new != content:
        content = new
        print(f"✅ Updated body position")

with open("body.py","w") as f:
    f.write(content)

# Update main.py Point B
with open("main.py","r") as f:
    main = f.read()
main = re.sub(
    r'POINT_B\s*=\s*\[.*?\]',
    f'POINT_B = [{TARGET[0]:.3f}, {TARGET[1]:.3f}, {TARGET[2]+0.01:.3f}]',
    main)
with open("main.py","w") as f:
    f.write(main)

print(f"\n✅ Done! Point B = {TARGET}")
print("Run: python3 main.py")
