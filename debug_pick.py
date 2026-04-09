import mujoco
import numpy as np
from body import RobotBody

robot = RobotBody()
mujoco.mj_forward(robot.model, robot.data)

r_wrist = mujoco.mj_name2id(
    robot.model, mujoco.mjtObj.mjOBJ_BODY,
    'right_wrist_yaw_link')
cube = mujoco.mj_name2id(
    robot.model, mujoco.mjtObj.mjOBJ_BODY,
    'red_cube')

wrist_pos = robot.data.xpos[r_wrist]
cube_pos  = robot.data.xpos[cube]

print(f"Wrist: {wrist_pos}")
print(f"Cube:  {cube_pos}")
print(f"Gap:   {np.linalg.norm(wrist_pos-cube_pos):.4f}m")

# Print all contacts at start
print(f"\nContacts at neutral: {robot.data.ncon}")
for i in range(robot.data.ncon):
    c  = robot.data.contact[i]
    b1 = robot.model.geom_bodyid[c.geom1]
    b2 = robot.model.geom_bodyid[c.geom2]
    n1 = robot.model.body(b1).name
    n2 = robot.model.body(b2).name
    if 'cube' in n1 or 'cube' in n2:
        print(f"  cube contact: {n1} <-> {n2} dist={c.dist:.4f}")
