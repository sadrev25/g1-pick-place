import mujoco
import numpy as np
import os, re, time
import mujoco.viewer

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

def hold(n=300):
    for _ in range(n):
        mujoco.mj_step(model, data)
        if viewer.is_running():
            viewer.sync()
        time.sleep(0.002)

# NEW object position — within workspace!
obj = np.array([0.28, -0.10, 0.82])
print(f"Object at: {obj}")
print(f"Workspace: X=-0.36 to 0.43, "
      f"Y=-0.50 to 0.12, Z=0.75 to 1.38")

with mujoco.viewer.launch_passive(
        model, data) as viewer:

    hold(200)
    w = get_wrist()
    print(f"\nNeutral wrist: {w}")
    print(f"Gap neutral: "
          f"{np.linalg.norm(obj-w):.3f}m")

    # With new object position
    # gap should be small already!
    # IK should converge without posture

    print("\n=== TEST: No posture needed? ===")
    best_gap   = 999
    best_combo = {}

    for c10 in [-0.3,-0.5,-0.8,-1.0]:
        for c11 in [-0.3,-0.5,-0.8,-1.0]:
            for c13 in [-0.3,-0.5,-0.8,-1.0]:
                data.ctrl[:] = 0
                data.ctrl[10] = c10
                data.ctrl[11] = c11
                data.ctrl[13] = c13
                for _ in range(300):
                    mujoco.mj_step(model,data)
                mujoco.mj_forward(model,data)
                w = data.xpos[r_wrist].copy()
                g = np.linalg.norm(obj-w)
                if g < best_gap:
                    best_gap   = g
                    best_combo = {
                        'c10': c10,
                        'c11': c11,
                        'c13': c13,
                        'wrist': w
                    }

    print(f"Best gap: {best_gap:.3f}m")
    print(f"Best combo: {best_combo}")

    # Show best
    data.ctrl[:] = 0
    data.ctrl[10] = best_combo['c10']
    data.ctrl[11] = best_combo['c11']
    data.ctrl[13] = best_combo['c13']
    hold(600)

    print(f"\nFinal wrist: {get_wrist()}")
    print(f"Object:      {obj}")
    print(f"Gap:         "
          f"{np.linalg.norm(obj-get_wrist()):.3f}m")

    while viewer.is_running():
        mujoco.mj_step(model, data)
        viewer.sync()
        time.sleep(0.002)
