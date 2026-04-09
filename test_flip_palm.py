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

def get_palm_up():
    """Returns z component of wrist z-axis.
    +1 = palm UP, -1 = palm DOWN"""
    mujoco.mj_forward(robot.model, robot.data)
    mat = robot.data.xmat[wrist_id].reshape(3,3)
    return mat[:,2][2]

print("Goal: flip palm from UP to DOWN")
print("Neutral palm_up = +0.995")
print("Target palm_up  = -1.0")
print()

# Try combinations that flip z-axis
combos = [
    # roll is the key — it rotates around x
    # need ~180 deg = π = 3.14 rad
    # but limit is 1.97 so try max
    {"26": +1.97, "27":  0.00, "label": "max roll only"},
    {"26": -1.97, "27":  0.00, "label": "neg roll only"},
    {"26": +1.97, "27": -1.61, "label": "max roll+pitch"},
    {"26": -1.97, "27": -1.61, "label": "neg roll+pitch"},
    {"26": +1.97, "27": +1.61, "label": "max roll pos pitch"},
    {"26": -1.97, "27": +1.61, "label": "neg roll pos pitch"},
    # Try elbow to orient arm first
    {"25": +2.0,  "26": +1.97, "27": -1.61,
     "label": "elbow+roll+pitch"},
    {"25": +2.0,  "26": -1.97, "27": -1.61,
     "label": "elbow+negroll+pitch"},
]

best_z   = 999
best_combo = None

for combo in combos:
    label = combo.pop("label")
    robot.data.ctrl[:] = 0
    for _ in range(100):
        mujoco.mj_step(robot.model, robot.data)

    for idx_str, val in combo.items():
        robot.data.ctrl[int(idx_str)] = val

    for _ in range(300):
        mujoco.mj_step(robot.model, robot.data)
        robot.viewer.sync()
        time.sleep(0.003)

    z    = get_palm_up()
    good = "✅ PALM DOWN!" if z < -0.5 else (
           "close" if z < 0 else "❌")
    print(f"{label:30s} palm_z={z:+.3f} {good}")

    if z < best_z:
        best_z     = z
        best_combo = (label, combo)

print(f"\nBest: {best_z:.3f}")
