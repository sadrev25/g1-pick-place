import mujoco
import mujoco.viewer
import numpy as np
import time, os, re

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

with mujoco.viewer.launch_passive(
        model, data) as viewer:

    hold(200)

    print("=== WHAT MOVES WRIST FORWARD (x)? ===")
    print(f"Need x={obj[0]:.2f} "
          f"currently x=0.20")
    print()

    # Test ALL joints one by one
    # Find which one increases x most
    for i in range(17):
        name = model.actuator(i).name
        best_x = -999
        best_v = 0

        for v in [-2.0,-1.5,-1.0,-0.5,
                   0.5, 1.0, 1.5, 2.0]:
            data.ctrl[:] = 0
            data.ctrl[i] = v
            for _ in range(200):
                mujoco.mj_step(model, data)
            mujoco.mj_forward(model, data)
            w = data.xpos[r_wrist]
            if w[0] > best_x:
                best_x = w[0]
                best_v = v

        data.ctrl[:] = 0
        for _ in range(100):
            mujoco.mj_step(model, data)

        print(f"ctrl[{i:2d}] {name:30s} "
              f"max_x={best_x:.3f} "
              f"at val={best_v:+.1f}")

    print("\n=== COMBINE BEST X JOINTS ===")
    # Now try combinations that maximize x
    # while keeping y~-0.15 and z~0.44

    best_gap   = 999
    best_combo = {}

    # From above test, use joints that gave x>0.4
    # Try systematic combinations
    for c2 in [0.3, 0.5, 0.7]:      # waist pitch
        for c10 in [-0.5, -1.0]:     # r shoulder
        # shoulder roll helps y and z
            for c11 in [-0.5,-1.0,-1.5,-2.0]:
                for c13 in [-0.5,-1.0,-1.5]:  # elbow
                    data.ctrl[:] = 0
                    data.ctrl[2]  = c2
                    data.ctrl[10] = c10
                    data.ctrl[11] = c11
                    data.ctrl[13] = c13
                    for _ in range(300):
                        mujoco.mj_step(model,data)
                    mujoco.mj_forward(model,data)
                    w   = data.xpos[r_wrist]
                    gap = np.linalg.norm(obj - w)
                    if gap < best_gap:
                        best_gap   = gap
                        best_combo = {
                            'waist_pitch':    c2,
                            'r_shoulder_p':   c10,
                            'r_shoulder_r':   c11,
                            'r_elbow':        c13,
                            'wrist':          w.copy()
                        }

    print(f"\nBest combination:")
    for k,v in best_combo.items():
        print(f"  {k}: {v}")
    print(f"Best gap: {best_gap:.3f}m")

    # Show it
    data.ctrl[:] = 0
    data.ctrl[2]  = best_combo['waist_pitch']
    data.ctrl[10] = best_combo['r_shoulder_p']
    data.ctrl[11] = best_combo['r_shoulder_r']
    data.ctrl[13] = best_combo['r_elbow']
    hold(600)

    print(f"\nFinal wrist: {get_wrist()}")
    print(f"Object at:   {obj}")
    print(f"Final gap:   "
          f"{np.linalg.norm(obj-get_wrist()):.3f}m")

    while viewer.is_running():
        mujoco.mj_step(model, data)
        viewer.sync()
        time.sleep(0.002)
