import numpy as np
import pickle
import mujoco
import os
import sys
sys.path.append(os.path.dirname(
    os.path.abspath(__file__)))
from body import RobotBody
from ik_controller import IKController

OBJ_BASE = np.array([0.230, -0.149, 0.878])
TARGET   = np.array([0.130, -0.299, 0.878])
ARM_CTRL = [22, 23, 24, 25, 26, 27, 28]

def setup():
    robot = RobotBody()
    ik    = IKController(
        robot.model, robot.data, None)
    return robot, ik

def get_state(robot, ik):
    hand   = ik.get_ee_pos('right')
    bid    = mujoco.mj_name2id(
        robot.model,
        mujoco.mjtObj.mjOBJ_BODY,
        'red_cube')
    mujoco.mj_forward(
        robot.model, robot.data)
    obj    = robot.data.xpos[bid].copy()
    joints = np.array([
        robot.data.ctrl[i]
        for i in ARM_CTRL],
        dtype=np.float32)
    return np.concatenate([
        hand, obj, TARGET, joints
    ]).astype(np.float32)

def get_action(robot):
    return np.array([
        robot.data.ctrl[i]
        for i in ARM_CTRL],
        dtype=np.float32)

def set_obj_pos(robot, pos):
    bid = mujoco.mj_name2id(
        robot.model,
        mujoco.mjtObj.mjOBJ_BODY,
        'red_cube')
    for j in range(robot.model.njnt):
        if robot.model.jnt_bodyid[j] == bid:
            adr = robot.model.jnt_qposadr[j]
            robot.data.qpos[adr:adr+3] = pos
            mujoco.mj_forward(
                robot.model, robot.data)
            break

def get_obj_pos(robot):
    bid = mujoco.mj_name2id(
        robot.model,
        mujoco.mjtObj.mjOBJ_BODY,
        'red_cube')
    mujoco.mj_forward(
        robot.model, robot.data)
    return robot.data.xpos[bid].copy()

def collect_one_demo(robot, ik):
    mujoco.mj_resetData(
        robot.model, robot.data)
    noise       = np.random.uniform(
        -0.03, 0.03, size=3)
    noise[2]    = 0
    obj_pos     = OBJ_BASE + noise
    set_obj_pos(robot, obj_pos)
    states  = []
    actions = []
    grasped = False
    above    = obj_pos.copy()
    above[2] += 0.10
    for _ in range(5):
        ik.ik_step(above, 'right')
        mujoco.mj_step(
            robot.model, robot.data)
    for step in range(300):
        state = get_state(robot, ik)
        if not grasped:
            ik_target = obj_pos.copy()
        else:
            ik_target = TARGET.copy()
        for _ in range(5):
            ik.ik_step(ik_target, 'right')
            mujoco.mj_step(
                robot.model, robot.data)
        action = get_action(robot)
        states.append(state)
        actions.append(action)
        hand = ik.get_ee_pos('right')
        obj  = get_obj_pos(robot)
        dist = np.linalg.norm(hand - obj)
        if dist < 0.08 and not grasped:
            grasped = True
            set_obj_pos(robot, hand)
        if grasped:
            set_obj_pos(robot, hand)
            dist_tgt = np.linalg.norm(
                hand - TARGET)
            if dist_tgt < 0.08:
                return {
                    "states":  np.array(states),
                    "actions": np.array(actions),
                    "success": True,
                    "length":  step}
    return {"success": False}

def collect_dataset(n_demos=100,
                    save_path="demos.pkl"):
    robot, ik = setup()
    dataset   = []
    attempts  = 0
    print(f"Collecting {n_demos} demos...")
    while len(dataset) < n_demos:
        attempts += 1
        demo = collect_one_demo(robot, ik)
        if demo["success"]:
            dataset.append(demo)
            print(
                f"Demo {len(dataset):3d}"
                f"/{n_demos} "
                f"steps={demo['length']:3d} "
                f"attempts={attempts}")
        else:
            print(f"Failed attempt {attempts}")
    with open(save_path, "wb") as f:
        pickle.dump(dataset, f)
    print(f"\nSaved {n_demos} demos!")
    print(f"Success rate: "
          f"{n_demos/attempts*100:.1f}%")
    print(f"Avg length: "
          f"{np.mean([d['length'] for d in dataset]):.1f}")
    print(f"State dim: "
          f"{dataset[0]['states'].shape[1]}")
    print(f"Action dim: "
          f"{dataset[0]['actions'].shape[1]}")
    return dataset

if __name__ == "__main__":
    dataset = collect_dataset(
        n_demos=100,
        save_path="demos.pkl")
    print("Next: python3 train_bc.py")
