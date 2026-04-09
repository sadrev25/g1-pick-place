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

print("Finding natural palm-down pose...")
print("Varying shoulder pitch smoothly")
print()

# Keep wrist at limits, vary shoulder
for s22 in [-0.3, -0.5, -0.7, -0.9, -1.0]:
    robot.data.ctrl[:] = 0
    for _ in range(100):
        mujoco.mj_step(robot.model, robot.data)

    robot.data.ctrl[27] = -1.61
    robot.data.ctrl[26] = +1.97
    robot.data.ctrl[22] = s22

    for _ in range(300):
        mujoco.mj_step(robot.model, robot.data)
        robot.viewer.sync()
        time.sleep(0.003)

    z    = get_palm_z()
    good = "✅" if z < -0.5 else "close" if z < -0.2 else "❌"
    print(f"shoulder={s22:+.1f} "
          f"palm_z={z:+.3f} {good}")

print("\nDone!")
