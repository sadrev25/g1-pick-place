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
    return mat[:,2][2]

print("Testing: reach forward + palm down")
print("Watch viewer!")

# Step 1: reach arm forward (like picking)
print("\nStep 1: Arm reaches forward...")
robot.data.ctrl[22] = -0.5  # shoulder pitch
robot.data.ctrl[25] = +0.5  # elbow
for _ in range(200):
    mujoco.mj_step(robot.model, robot.data)
    robot.viewer.sync()
    time.sleep(0.005)
print(f"palm_z = {get_palm_z():.3f}")

# Step 2: add wrist roll to face down
print("\nStep 2: Rotate wrist down...")
for s in range(100):
    a = s / 100
    a = a * a * (3 - 2 * a)
    robot.data.ctrl[26] = a * (-1.97)
    mujoco.mj_step(robot.model, robot.data)
    robot.viewer.sync()
    time.sleep(0.005)
print(f"palm_z = {get_palm_z():.3f}")
print("Does palm face DOWN toward table now?")

# Hold for 3 seconds to observe
for _ in range(150):
    mujoco.mj_step(robot.model, robot.data)
    robot.viewer.sync()
    time.sleep(0.02)

print("Done!")
