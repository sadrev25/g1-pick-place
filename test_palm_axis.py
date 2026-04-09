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

# Apply the "palm down" combo we found
robot.data.ctrl[27] = -1.61
robot.data.ctrl[26] = +1.97
robot.data.ctrl[22] = -0.7

for _ in range(300):
    mujoco.mj_step(robot.model, robot.data)
    robot.viewer.sync()
    time.sleep(0.003)

mujoco.mj_forward(robot.model, robot.data)
mat = robot.data.xmat[wrist_id].reshape(3,3)

print("=== WRIST ROTATION MATRIX ===")
print(f"x-axis (forward): {mat[:,0].round(3)}")
print(f"y-axis (sideways):{mat[:,1].round(3)}")
print(f"z-axis (up/down): {mat[:,2].round(3)}")
print()
print("Which axis points toward floor [0,0,-1]?")
print(f"x toward floor: {-mat[:,0][2]:.3f}")
print(f"y toward floor: {-mat[:,1][2]:.3f}")
print(f"z toward floor: {-mat[:,2][2]:.3f}")
print()

# Also check neutral pose
robot.data.ctrl[:] = 0
for _ in range(200):
    mujoco.mj_step(robot.model, robot.data)
robot.viewer.sync()

mujoco.mj_forward(robot.model, robot.data)
mat2 = robot.data.xmat[wrist_id].reshape(3,3)
print("=== NEUTRAL WRIST AXES ===")
print(f"x-axis: {mat2[:,0].round(3)}")
print(f"y-axis: {mat2[:,1].round(3)}")
print(f"z-axis: {mat2[:,2].round(3)}")
print()
print("Neutral palm faces which direction?")
print(f"x: {'DOWN' if mat2[:,0][2]<-0.5 else 'UP' if mat2[:,0][2]>0.5 else 'sideways'}")
print(f"y: {'DOWN' if mat2[:,1][2]<-0.5 else 'UP' if mat2[:,1][2]>0.5 else 'sideways'}")
print(f"z: {'DOWN' if mat2[:,2][2]<-0.5 else 'UP' if mat2[:,2][2]>0.5 else 'sideways'}")
