import mujoco
import mujoco.viewer
import numpy as np
import time
import os

with open(os.path.expanduser(
    '~/mujoco_menagerie/unitree_g1/scene.xml')) as f:
    xml = f.read()

objects = """
<body name="table" pos="0.65 0 0.38">
  <geom type="box" size="0.4 0.3 0.02"
        rgba="0.6 0.4 0.2 1" mass="20"/>
  <inertial pos="0 0 0" mass="20"
            diaginertia="1 1 1"/>
</body>
<body name="red_cube" pos="0.60 -0.15 0.44">
  <joint type="free"/>
  <geom type="box" size="0.04 0.04 0.04"
        rgba="0.9 0.2 0.2 1" mass="0.3"/>
  <inertial pos="0 0 0" mass="0.3"
            diaginertia="0.001 0.001 0.001"/>
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
cube_id = mujoco.mj_name2id(
    model, mujoco.mjtObj.mjOBJ_BODY,
    'red_cube')

def get_wrist():
    mujoco.mj_forward(model, data)
    return data.xpos[r_wrist].copy()

def get_cube():
    mujoco.mj_forward(model, data)
    return data.xpos[cube_id].copy()

def step(n=1):
    for _ in range(n):
        mujoco.mj_step(model, data)
        if viewer.is_running():
            viewer.sync()
        time.sleep(0.002)

print("UNDERSTANDING IK STEP BY STEP")
print("Watch the terminal + viewer together")

with mujoco.viewer.launch_passive(
        model, data) as viewer:

    step(200)

    # Phase 1 — show the problem
    print("\n=== PHASE 1: Problem (no posture) ===")
    cube = get_cube()
    wrist = get_wrist()
    print(f"Cube:  {cube}")
    print(f"Wrist: {wrist}")
    print(f"Gap:   {np.linalg.norm(cube-wrist):.3f}m")
    print("Too far for IK to converge alone!")
    step(500)

    # Phase 2 — fix posture first
    print("\n=== PHASE 2: Fix posture first ===")
    print("Step 2a: Lean waist forward...")
    data.ctrl[14] = 0.4    # waist pitch
    step(400)
    print(f"Wrist now: {get_wrist()}")

    print("Step 2b: Shoulder forward manually...")
    data.ctrl[22] = 1.0    # shoulder pitch
    step(400)
    print(f"Wrist now: {get_wrist()}")

    print("Step 2c: Elbow bend...")
    data.ctrl[25] = -1.0   # elbow
    step(400)
    print(f"Wrist now: {get_wrist()}")

    cube  = get_cube()
    wrist = get_wrist()
    gap   = np.linalg.norm(cube - wrist)
    print(f"\nAfter posture: gap = {gap:.3f}m")
    print("NOW IK only needs small correction!")

    # Phase 3 — IK from good starting point
    print("\n=== PHASE 3: IK from good posture ===")
    target = cube.copy()
    target[2] += 0.18   # above cube

    r_dofs  = [28,29,30,31,32,33,34]
    r_ctrls = [22,23,24,25,26,27,28]
    r_limits = [
        (-1.5,3.0),(-2.5,0.5),(-1.5,1.5),
        (-2.5,0.0),(-1.5,1.5),(-1.0,1.0),(-1.5,1.5)
    ]

    for step_n in range(2000):
        current = get_wrist()
        error   = target - current
        err_mag = np.linalg.norm(error)

        if err_mag < 0.04:
            print(f"✅ Reached! err={err_mag:.4f}m "
                  f"steps={step_n}")
            break

        # Clamp step size
        if err_mag > 0.03:
            error = error * 0.03 / err_mag

        # Jacobian
        jacp = np.zeros((3, model.nv))
        jacr = np.zeros((3, model.nv))
        mujoco.mj_jac(model, data, jacp, jacr,
                       current, r_wrist)

        J = jacp[:, r_dofs]

        # Damped pseudoinverse
        lam    = 0.05
        J_pinv = J.T @ np.linalg.inv(
            J @ J.T + lam * np.eye(3))
        dq = J_pinv @ error * 0.15

        # Apply with limits
        for i, ctrl_idx in enumerate(r_ctrls):
            new_v = data.ctrl[ctrl_idx] + dq[i]
            lo,hi = r_limits[i]
            data.ctrl[ctrl_idx] = np.clip(
                new_v, lo, hi)

        mujoco.mj_step(model, data)
        viewer.sync()
        time.sleep(0.002)

        if step_n % 200 == 0:
            print(f"  step={step_n:4d} "
                  f"err={err_mag:.4f}m "
                  f"wrist={current}")

    print("\nKey insight:")
    print("Good starting posture = IK converges fast")
    print("Bad starting posture  = IK oscillates")

    step(500)
