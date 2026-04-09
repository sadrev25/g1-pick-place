from body import RobotBody
import mujoco
import numpy as np
import time

robot = RobotBody()
robot.start()

wrist_id = mujoco.mj_name2id(
    robot.model,
    mujoco.mjtObj.mjOBJ_BODY,
    'right_wrist_yaw_link')

def get_palm_z():
    mujoco.mj_forward(robot.model, robot.data)
    mat = robot.data.xmat[wrist_id].reshape(3,3)
    return mat[:, 2][2]

# Print joint limits first
print("=== JOINT LIMITS ===")
for idx in [26, 27, 28]:
    name = robot.model.actuator(idx).name
    jid  = mujoco.mj_name2id(
        robot.model,
        mujoco.mjtObj.mjOBJ_JOINT, name)
    lo = robot.model.jnt_range[jid][0]
    hi = robot.model.jnt_range[jid][1]
    print(f"ctrl[{idx}] {name:30s} "
          f"[{lo:.2f} to {hi:.2f}]")

print("\n=== TESTING AT JOINT LIMITS ===")
combos = [
    # Push to absolute limits
    (27, -1.61, 26, +1.97),
    (27, -1.61, 26, +1.50),
    (27, -1.20, 26, +1.97),
    # Try shoulder pitch to help
    (27, -1.61, 26, +1.97, 22, -1.0),
    (27, -1.61, 26, +1.97, 25, +1.5),
]

for combo in combos:
    # Reset
    robot.data.ctrl[:] = 0
    for _ in range(100):
        mujoco.mj_step(robot.model, robot.data)

    # Apply
    label = ""
    for i in range(0, len(combo), 2):
        idx = combo[i]
        val = combo[i+1]
        robot.data.ctrl[idx] = val
        label += f"ctrl[{idx}]={val:+.2f} "

    for _ in range(300):
        mujoco.mj_step(robot.model, robot.data)
        robot.viewer.sync()
        time.sleep(0.003)

    z    = get_palm_z()
    good = "✅ PALM DOWN!" if z < -0.5 else (
           "close!" if z < -0.1 else "❌")
    print(f"{label}")
    print(f"  palm_z={z:+.3f} {good}\n")

print("Done!")
