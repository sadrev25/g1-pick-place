import numpy as np
import gymnasium as gym
import mujoco
import os
import sys
sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__))))

class ResidualPickEnv(gym.Env):

    OBJ_BASE = np.array([0.230, -0.149, 0.878])
    TARGET   = np.array([0.130, -0.299, 0.878])

    def __init__(self, render=False):
        super().__init__()
        self.render_mode = render

        self.observation_space = gym.spaces.Box(
            low=-np.inf, high=np.inf,
            shape=(10,), dtype=np.float32)

        self.action_space = gym.spaces.Box(
            low=-0.05, high=0.05,
            shape=(3,), dtype=np.float32)

        self._setup()

    def _setup(self):
        from body import RobotBody
        from ik_controller import IKController

        self.robot = RobotBody()
        if self.render_mode:
            self.robot.start()

        self.ik = IKController(
            self.robot.model,
            self.robot.data,
            self.robot.viewer
            if self.render_mode else None)

        self.grasped   = False
        self.phase     = 0
        self.steps     = 0
        self.MAX_STEPS = 500

    def _get_obj_pos(self):
        bid = mujoco.mj_name2id(
            self.robot.model,
            mujoco.mjtObj.mjOBJ_BODY,
            'red_cube')
        if bid < 0:
            return self.OBJ_BASE.copy()
        mujoco.mj_forward(
            self.robot.model,
            self.robot.data)
        return self.robot.data.xpos[bid].copy()

    def _set_obj_pos(self, pos):
        bid = mujoco.mj_name2id(
            self.robot.model,
            mujoco.mjtObj.mjOBJ_BODY,
            'red_cube')
        for j in range(self.robot.model.njnt):
            if self.robot.model.jnt_bodyid[j] \
                    == bid:
                adr = self.robot.model\
                    .jnt_qposadr[j]
                self.robot.data.qpos[
                    adr:adr+3] = pos
                mujoco.mj_forward(
                    self.robot.model,
                    self.robot.data)
                break

    def _get_obs(self):
        hand = self.ik.get_ee_pos('right')
        obj  = self._get_obj_pos()
        tgt  = self.TARGET.copy()
        ph   = np.array([self.phase / 3.0])
        return np.concatenate(
            [hand, obj, tgt, ph]
        ).astype(np.float32)

    def step(self, residual):
        self.steps += 1

        hand    = self.ik.get_ee_pos('right')
        obj_pos = self._get_obj_pos()

        # IK target with residual correction
        if not self.grasped:
            ik_target = obj_pos + residual
        else:
            ik_target = self.TARGET + residual

        # Run 5 IK steps per env step
        # so arm actually moves meaningfully
        for _ in range(5):
            self.ik.ik_step(
                ik_target, 'right')
            mujoco.mj_step(
                self.robot.model,
                self.robot.data)

        if self.render_mode and \
                self.robot.viewer and \
                self.robot.viewer.is_running():
            self.robot.viewer.sync()

        hand    = self.ik.get_ee_pos('right')
        obj_pos = self._get_obj_pos()

        dist_obj = np.linalg.norm(
            hand - obj_pos)
        reward   = -dist_obj * 2.0

        # Grasp — threshold 0.08m
        if dist_obj < 0.08 and \
                not self.grasped:
            self.grasped = True
            self.phase   = 1
            reward      += 5.0
            self._set_obj_pos(hand)

        # Place
        if self.grasped:
            self._set_obj_pos(hand)
            dist_tgt = np.linalg.norm(
                hand - self.TARGET)
            reward  += -dist_tgt * 2.0

            if dist_tgt < 0.08:
                reward += 10.0
                return (self._get_obs(),
                        reward,
                        True, False, {})

        reward -= 0.01 * np.linalg.norm(
            residual)

        truncated = self.steps >= self.MAX_STEPS
        return (self._get_obs(),
                reward,
                False, truncated, {})

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        mujoco.mj_resetData(
            self.robot.model,
            self.robot.data)

        self.grasped = False
        self.phase   = 0
        self.steps   = 0

        noise       = np.random.uniform(
            -0.04, 0.04, size=3)
        noise[2]    = 0
        new_pos     = self.OBJ_BASE + noise
        self._set_obj_pos(new_pos)

        return self._get_obs(), {}
