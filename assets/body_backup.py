import mujoco
import mujoco.viewer
import numpy as np
import time
import os
import re
from joint_map import JOINT_MAP

def build_welded_scene():
    g1_dir = os.path.expanduser(
        "~/mujoco_menagerie/unitree_g1")

    with open(f"{g1_dir}/scene.xml") as f:
        scene = f.read()
    with open(f"{g1_dir}/g1.xml") as f:
        g1 = f.read()

    leg_joints = [
        "left_hip_pitch_joint",
        "left_hip_roll_joint",
        "left_hip_yaw_joint",
        "left_knee_joint",
        "left_ankle_pitch_joint",
        "left_ankle_roll_joint",
        "right_hip_pitch_joint",
        "right_hip_roll_joint",
        "right_hip_yaw_joint",
        "right_knee_joint",
        "right_ankle_pitch_joint",
        "right_ankle_roll_joint",
    ]

    g1 = g1.replace(
        "<freejoint name=\"floating_base_joint\"/>", "")
    for j in leg_joints:
        g1 = re.sub(
            r"<joint name=\""+j+r"\"[^/]*//>", "", g1)
        g1 = re.sub(
            r"<position[^>]*joint=\""+j+r"\"[^/]*//>", "", g1)
    g1 = re.sub(
        r"<keyframe>.*?</keyframe>", "", g1,
        flags=re.DOTALL)
    scene = re.sub(
        r"<keyframe>.*?</keyframe>", "", scene,
        flags=re.DOTALL)

    with open(f"{g1_dir}/g1_fixed.xml", "w") as f:
        f.write(g1)
    scene = scene.replace(
        "<include file=\"g1.xml\"/>",
        "<include file=\"g1_fixed.xml\"/>")

    # Wrist measured at [0.200, -0.149, 0.888]
    # Table in front at x=0.35, same y and z
    # Objects on table surface = table_z + 0.01 + 0.04
    # NO container walls — just flat pad, robot hand
    # passes through (arm collision disabled in IK)
    objects = """
    <body name="table" pos="0.230 -0.149 0.828">
      <geom type="box" size="0.22 0.20 0.01"
            rgba="0.65 0.40 0.15 1"
            mass="500" contype="1" conaffinity="1"
            friction="1.5 0.05 0.05"/>
      <inertial pos="0 0 0" mass="500"
                diaginertia="100 100 100"/>
    </body>

    <body name="red_cube" pos="0.230 -0.149 0.878">
      <joint type="free"/>
      <geom type="box" size="0.04 0.04 0.04"
            rgba="0.9 0.2 0.2 1" mass="0.5"
            contype="1" conaffinity="1"
            friction="2.0 0.5 0.5"
            solimp="0.99 0.999 0.001"
            solref="0.01 1"/>
      <inertial pos="0 0 0" mass="0.5"
                diaginertia="0.01 0.01 0.01"/>
    </body>

    <body name="blue_cube" pos="0.230 -0.030 0.878">
      <joint type="free"/>
      <geom type="box" size="0.035 0.035 0.035"
            rgba="0.2 0.2 0.9 1" mass="0.5"
            contype="1" conaffinity="1"
            friction="2.0 0.5 0.5"
            solimp="0.99 0.999 0.001"
            solref="0.01 1"/>
      <inertial pos="0 0 0" mass="0.5"
                diaginertia="0.01 0.01 0.01"/>
    </body>

    <body name="green_cylinder" pos="0.230 -0.270 0.878">
      <joint type="free"/>
      <geom type="cylinder" size="0.035 0.04"
            rgba="0.2 0.8 0.2 1" mass="0.5"
            contype="1" conaffinity="1"
            friction="2.0 0.5 0.5"
            solimp="0.99 0.999 0.001"
            solref="0.01 1"/>
      <inertial pos="0 0 0" mass="0.5"
                diaginertia="0.01 0.01 0.01"/>
    </body>

    <body name="place_target"
          pos="0.230 -0.149 0.818">
      <geom type="box" size="0.12 0.12 0.01"
            rgba="0.2 0.9 0.2 0.5"
            mass="500" contype="1" conaffinity="1"
            friction="2.0 0.5 0.5"/>
      <inertial pos="0 0 0" mass="500"
                diaginertia="100 100 100"/>
    </body>
"""
    scene = scene.replace(
        "</worldbody>",
        objects + "</worldbody>")

    return scene, g1_dir


class RobotBody:

    def __init__(self):
        self._load()

    def _load(self):
        scene_xml, g1_dir = build_welded_scene()
        os.chdir(g1_dir)
        self.model = mujoco.MjModel.from_xml_string(
            scene_xml)
        self.data  = mujoco.MjData(self.model)
        os.chdir(os.path.expanduser("~"))
        print(f"✅ Robot loaded!")
        print(f"   nv={self.model.nv} "
              f"nu={self.model.nu}")

    def start(self):
        self.viewer = mujoco.viewer.launch_passive(
            self.model, self.data)
        self._step(300)
        print("✅ Viewer ready!")

    def execute(self, result, steps=350):
        if not result:
            return
        joints = result.get("joints", {})
        if not joints:
            self._smooth_to(
                np.zeros(self.model.nu), steps=400)
            return
        target = self.data.ctrl.copy()
        for name, value in joints.items():
            if name in JOINT_MAP:
                idx = JOINT_MAP[name]["ctrl"]
                target[idx] = value
        self._smooth_to(target, steps)

    def _smooth_to(self, target, steps=350):
        start = self.data.ctrl.copy()
        for i in range(steps):
            a = i / steps
            a = a * a * (3 - 2 * a)
            self.data.ctrl[:] = (
                start + a * (target - start))
            self._step(1)

    def _step(self, n=1):
        for _ in range(n):
            mujoco.mj_step(self.model, self.data)
            if (hasattr(self, "viewer") and
                    self.viewer.is_running()):
                self.viewer.sync()
            time.sleep(0.002)

    def reset(self):
        self._smooth_to(
            np.zeros(self.model.nu), steps=400)

    def is_running(self):
        return (hasattr(self, "viewer") and
                self.viewer.is_running())

    def get_object_pos(self, name):
        bid = mujoco.mj_name2id(
            self.model,
            mujoco.mjtObj.mjOBJ_BODY, name)
        if bid == -1:
            return None
        mujoco.mj_forward(self.model, self.data)
        return self.data.xpos[bid].copy()

    def check_contact(self, body_name):
        bid = mujoco.mj_name2id(
            self.model,
            mujoco.mjtObj.mjOBJ_BODY, body_name)
        for i in range(self.data.ncon):
            c  = self.data.contact[i]
            b1 = self.model.geom_bodyid[c.geom1]
            b2 = self.model.geom_bodyid[c.geom2]
            if b1 == bid or b2 == bid:
                return True
        return False
