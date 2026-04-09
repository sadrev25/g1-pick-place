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
    return mat[:, 2]

print("Testing positive values on wrist joints")
print("Neutral palm_z = +0.999")
print("Want palm_z = -1.0 (facing DOWN)")
print()

# Test both +1.0 and -1.0 for joints 26,27,28
for idx in [26, 27, 28]:
    name = robot.model.actuator(idx).name
    for val in [+1.0, +1.5, -1.0, -1.5]:
        # Reset
        robot.data.ctrl[:] = 0
        for _ in range(100):
            mujoco.mj_step(
                robot.model, robot.data)

        # Apply value
        robot.data.ctrl[idx] = val
        for _ in range(200):
            mujoco.mj_step(
                robot.model, robot.data)
            robot.viewer.sync()
            time.sleep(0.003)

        palm = get_palm_z()
        z    = palm[2]
        good = "✅ PALM DOWN!" if z < -0.3 else ""
        print(f"ctrl[{idx}]={val:+.1f} "
              f"{name:30s} "
              f"palm_z={z:+.3f} {good}")

    print()

print("Done!")
