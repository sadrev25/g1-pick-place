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

print("Testing combined wrist joints")
print("Want palm_z < -0.5")
print()

combos = [
    (27, -1.5, 26, +1.5),
    (27, -1.5, 26, +2.0),
    (27, -1.6, 26, +1.9),
    (27, -1.5, 26, +1.0),
    (27, -1.0, 26, +1.5),
]

for p_idx, p_val, r_idx, r_val in combos:
    # Reset
    robot.data.ctrl[:] = 0
    for _ in range(100):
        mujoco.mj_step(robot.model, robot.data)

    # Apply both
    robot.data.ctrl[p_idx] = p_val
    robot.data.ctrl[r_idx] = r_val
    for _ in range(200):
        mujoco.mj_step(robot.model, robot.data)
        robot.viewer.sync()
        time.sleep(0.003)

    z    = get_palm_z()
    good = "✅ PALM DOWN!" if z < -0.3 else "❌"
    print(f"pitch={p_val:+.1f} "
          f"roll={r_val:+.1f} "
          f"palm_z={z:+.3f} {good}")

print("\nDone!")
