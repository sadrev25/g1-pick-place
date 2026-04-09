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

def get_palm_direction():
    mujoco.mj_forward(robot.model, robot.data)
    mat = robot.data.xmat[wrist_id].reshape(3,3)
    # z-axis of wrist = palm normal direction
    # if z points DOWN [0,0,-1] = palm faces table
    return mat[:, 2]  # palm normal

print("=== NEUTRAL PALM DIRECTION ===")
palm = get_palm_direction()
print(f"Palm normal: {palm.round(3)}")
print(f"z component: {palm[2]:.3f}")
print(f"(want z=-1.0 = palm faces DOWN)")

print("\n=== TESTING EACH WRIST JOINT ===")
for idx in range(22, 29):
    name = robot.model.actuator(idx).name

    # Reset all to 0
    robot.data.ctrl[:] = 0
    for _ in range(100):
        mujoco.mj_step(robot.model, robot.data)
    robot.viewer.sync()

    # Apply -1.0 to this joint
    robot.data.ctrl[idx] = -1.0
    for _ in range(200):
        mujoco.mj_step(robot.model, robot.data)
        robot.viewer.sync()
        time.sleep(0.005)

    palm = get_palm_direction()
    z    = palm[2]
    good = "✅ PALM DOWN!" if z < -0.5 else "❌"
    print(f"ctrl[{idx}] {name:35s} "
          f"palm_z={z:+.3f} {good}")

    # Reset
    robot.data.ctrl[idx] = 0

print("\nDone!")
