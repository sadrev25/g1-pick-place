import mujoco
import numpy as np
import time

class IKController:

    def __init__(self, model, data, viewer):
        self.model   = model
        self.data    = data
        self.viewer  = viewer
        self.grasped = None  # currently held object

        self.r_wrist = mujoco.mj_name2id(
            model, mujoco.mjtObj.mjOBJ_BODY,
            'right_wrist_yaw_link')
        self.l_wrist = mujoco.mj_name2id(
            model, mujoco.mjtObj.mjOBJ_BODY,
            'left_wrist_yaw_link')

        # Verify wrist IDs found — crash early if not
        assert self.r_wrist >= 0, "right_wrist_yaw_link not found!"
        assert self.l_wrist >= 0, "left_wrist_yaw_link not found!"
        mujoco.mj_forward(model, data)
        print(f"   R wrist ID={self.r_wrist} "
              f"pos={data.xpos[self.r_wrist]}")
        print(f"   L wrist ID={self.l_wrist} "
              f"pos={data.xpos[self.l_wrist]}")

        self.r_arm_dofs  = [22,23,24,25,26,27,28]
        self.l_arm_dofs  = [15,16,17,18,19,20,21]
        self.r_arm_ctrls = [22,23,24,25,26,27,28]
        self.l_arm_ctrls = [15,16,17,18,19,20,21]

        self.r_limits = [
            (-1.5, 3.0),(-2.5, 0.5),
            (-1.5, 1.5),(-2.5, 0.0),
            (-1.5, 1.5),(-1.0, 1.0),
            (-1.5, 1.5),
        ]
        self.l_limits = [
            (-1.5, 3.0),(-0.5, 2.5),
            (-1.5, 1.5),(-2.5, 0.0),
            (-1.5, 1.5),(-1.0, 1.0),
            (-1.5, 1.5),
        ]

        # Disable collision on arm geoms
        # So hand passes through objects cleanly
        # Teleport grasp handles pick instead
        arm_bodies = [
            'right_shoulder_pitch_link',
            'right_shoulder_roll_link',
            'right_shoulder_yaw_link',
            'right_elbow_link',
            'right_wrist_roll_link',
            'right_wrist_pitch_link',
            'right_wrist_yaw_link',
            'left_shoulder_pitch_link',
            'left_shoulder_roll_link',
            'left_shoulder_yaw_link',
            'left_elbow_link',
            'left_wrist_roll_link',
            'left_wrist_pitch_link',
            'left_wrist_yaw_link',
        ]
        for i in range(model.ngeom):
            bid   = model.geom_bodyid[i]
            bname = model.body(bid).name
            if bname in arm_bodies:
                model.geom_contype[i]     = 0
                model.geom_conaffinity[i] = 0

        mujoco.mj_forward(model, data)
        print(f"✅ IK ready — arm collision disabled!")
        print(f"   R wrist: "
              f"{data.xpos[self.r_wrist]}")

    def set_wrist(self, pitch=0.0,
                   roll=0.0, yaw=0.0,
                   hand='right'):
        """
        Set wrist orientation directly.
        pitch: negative = palm faces DOWN
        roll:  rotate palm left/right
        yaw:   twist wrist
        """
        if hand == 'right':
            pitch_idx = 27
            roll_idx  = 26
            yaw_idx   = 28
        else:
            pitch_idx = 20
            roll_idx  = 19
            yaw_idx   = 21

        # Clamp to joint limits
        pitch = np.clip(pitch, -1.57, 1.57)
        roll  = np.clip(roll,  -1.90, 1.90)
        yaw   = np.clip(yaw,   -1.57, 1.57)

        self.data.ctrl[pitch_idx] = pitch
        self.data.ctrl[roll_idx]  = roll
        self.data.ctrl[yaw_idx]   = yaw

    def smooth_wrist(self, pitch=0.0,
                     roll=0.0, yaw=0.0,
                     hand='right', steps=80):
        """Smoothly transition wrist to pose."""
        if hand == 'right':
            idxs = [27, 26, 28]
        else:
            idxs = [20, 19, 21]

        targets = [pitch, roll, yaw]
        starts  = [self.data.ctrl[i]
                   for i in idxs]

        for s in range(steps):
            a = s / steps
            a = a * a * (3 - 2 * a)
            for i, idx in enumerate(idxs):
                self.data.ctrl[idx] = (
                    starts[i] +
                    a * (targets[i] - starts[i]))
            if self.grasped:
                self._carry_object()
            mujoco.mj_step(
                self.model, self.data)
            if self.viewer and                self.viewer.is_running():
                self.viewer.sync()
            import time
            time.sleep(0.002)

    def select_hand(self, obj_pos):
        hand = 'right'
        print(f'   Hand: {hand} (y={obj_pos[1]:.3f})')
        return hand

    def get_ee_pos(self, hand='right'):
        mujoco.mj_forward(self.model, self.data)
        bid = (self.r_wrist if hand=='right'
               else self.l_wrist)
        return self.data.xpos[bid].copy()

    def get_obj_pos(self, obj_name):
        bid = mujoco.mj_name2id(
            self.model,
            mujoco.mjtObj.mjOBJ_BODY, obj_name)
        mujoco.mj_forward(self.model, self.data)
        return self.data.xpos[bid].copy()

    def ik_step(self, target, hand='right',
                gain=0.15):
        bid = (self.r_wrist if hand=='right'
               else self.l_wrist)

        current = self.get_ee_pos(hand)
        error   = target - current

        err_mag = np.linalg.norm(error)
        if err_mag > 0.02:
            error = error * 0.02 / err_mag

        jacp = np.zeros((3, self.model.nv))
        jacr = np.zeros((3, self.model.nv))
        mujoco.mj_jac(
            self.model, self.data,
            jacp, jacr, current, bid)

        dofs   = (self.r_arm_dofs
                  if hand=='right'
                  else self.l_arm_dofs)
        ctrls  = (self.r_arm_ctrls
                  if hand=='right'
                  else self.l_arm_ctrls)
        limits = (self.r_limits
                  if hand=='right'
                  else self.l_limits)

        J = jacp[:, dofs]
        sv = np.linalg.svd(J, compute_uv=False)
        min_sv = sv[-1] if len(sv) > 0 else 1.0
        lam = 0.1 if min_sv > 0.1 else 0.5
        J_pinv = J.T @ np.linalg.inv(
            J @ J.T + lam * np.eye(3))
        dq = J_pinv @ error * gain

        for i, ctrl_idx in enumerate(ctrls):
            self.data.ctrl[ctrl_idx] = np.clip(
                self.data.ctrl[ctrl_idx] + dq[i],
                limits[i][0], limits[i][1])

        return np.linalg.norm(
            target - self.get_ee_pos(hand))

    def move_to(self, target, hand='right',
                tolerance=0.03, timeout=800,
                verbose=True):
        if verbose:
            ee   = self.get_ee_pos(hand)
            dist = np.linalg.norm(target - ee)
            print(f"   IK → "
                  f"[{target[0]:.3f},"
                  f"{target[1]:.3f},"
                  f"{target[2]:.3f}] "
                  f"dist={dist:.3f}m")

        best_err   = float('inf')
        no_improve = 0

        for step in range(timeout):
            # If holding object move it with arm
            if self.grasped:
                self._carry_object()

            err = self.ik_step(target, hand)
            mujoco.mj_step(self.model, self.data)
            if self.viewer.is_running():
                self.viewer.sync()
            time.sleep(0.002)

            if err < tolerance:
                if verbose:
                    print(f"   ✅ err={err:.4f}m"
                          f" steps={step}")
                return True

            if err < best_err - 0.0005:
                best_err   = err
                no_improve = 0
            else:
                no_improve += 1

            if no_improve > 800:
                if verbose:
                    print(f"   ⚠️ best"
                          f" err={err:.4f}m")
                break

        return err < tolerance * 2

    def _carry_object(self):
        """
        Move grasped object WITH the wrist
        This simulates a closed hand grip

        Get wrist position
        Set object position = wrist position
        Object follows arm exactly!
        """
        if not self.grasped:
            return

        obj_name, hand, offset = self.grasped

        # Find object joint qpos index
        obj_id = mujoco.mj_name2id(
            self.model,
            mujoco.mjtObj.mjOBJ_BODY,
            obj_name)

        # Find free joint for this object
        for j in range(self.model.njnt):
            if self.model.jnt_bodyid[j] == obj_id:
                jnt_type = self.model.jnt_type[j]
                if jnt_type == 0:  # free joint
                    qpos_idx = self.model.jnt_qposadr[j]

                    # Set position = wrist + offset
                    wrist_pos = self.get_ee_pos(hand)
                    # Dynamic palm offset using wrist orientation
                    # Palm is 0.15m along wrist x-axis
                    bid = (self.r_wrist if hand == 'right'
                           else self.l_wrist)
                    mat = self.data.xmat[bid].reshape(3, 3)
                    palm_dir    = mat[:, 0]  # wrist forward axis
                    palm_offset = palm_dir * 0.058
                    obj_pos = wrist_pos + offset + palm_offset

                    # Set position
                    self.data.qpos[qpos_idx]   = obj_pos[0]
                    self.data.qpos[qpos_idx+1] = obj_pos[1]
                    self.data.qpos[qpos_idx+2] = obj_pos[2]

                    # Keep orientation upright
                    self.data.qpos[qpos_idx+3] = 1.0
                    self.data.qpos[qpos_idx+4] = 0.0
                    self.data.qpos[qpos_idx+5] = 0.0
                    self.data.qpos[qpos_idx+6] = 0.0

                    # Zero velocity
                    dof = self.model.jnt_dofadr[j]
                    self.data.qvel[dof:dof+6] = 0
                    break

    def grasp_object(self, obj_name, hand='right'):
        """
        Attach object to wrist
        Object will follow arm from now on
        """
        wrist_pos = self.get_ee_pos(hand)
        obj_pos   = self.get_obj_pos(obj_name)

        # Store offset from wrist to object
        offset = np.zeros(3)
        self.grasped = (obj_name, hand, offset)
        print(f"   Grasped {obj_name}! "
              f"offset={offset}")

    def release_object(self):
        """Release grasped object"""
        if self.grasped:
            print(f"   Released {self.grasped[0]}!")
        self.grasped = None

    def pick_sequence(self, obj_name,
                       place_pos=None):
        print(f"\n{'='*40}")
        print(f"PICKING: {obj_name}")
        print(f"{'='*40}")

        obj_id = mujoco.mj_name2id(
            self.model,
            mujoco.mjtObj.mjOBJ_BODY, obj_name)

        if obj_id == -1:
            print(f"❌ {obj_name} not found!")
            return False

        mujoco.mj_forward(self.model, self.data)
        obj_pos = self.data.xpos[obj_id].copy()
        hand    = self.select_hand(obj_pos)
        ee_pos  = self.get_ee_pos(hand)
        gap     = np.linalg.norm(obj_pos - ee_pos)

        print(f"Object: {obj_pos}")
        print(f"Wrist:  {ee_pos}")
        print(f"Gap:    {gap:.3f}m")

        if gap > 0.5:
            print(f"❌ Too far!")
            return False

        # Step 0 — rotate wrist DOWN
        # ctrl[26] = wrist_roll = -1.97
        # This flips palm to face table
        import time
        print("\n[0] Rotating wrist down...")
        wr_start = self.data.ctrl[26]
        for s in range(100):
            a = s / 100
            a = a * a * (3 - 2 * a)
            self.data.ctrl[26] = (
                wr_start +
                a * (-1.97 - wr_start))
            mujoco.mj_step(
                self.model, self.data)
            if self.viewer and \
               self.viewer.is_running():
                self.viewer.sync()
            time.sleep(0.002)
        print("   Palm facing down!")

        # Step 1 — above object
        print("\n[1] Moving above object...")
        above     = obj_pos.copy()
        above[2] += 0.10
        ik_above = above
        ok = self.move_to(ik_above, hand)
        if not ok:
            print("❌ Cannot reach!")
            self._go_home()
            return False
        self._hold(150)

        # Step 2 — align XY with object
        print("\n[2] Aligning...")
        align    = obj_pos.copy()
        align[2] = self.get_ee_pos(hand)[2]
        self.move_to(align, hand, tolerance=0.02)
        self._hold(150)

        # Step 3 — move to EXACT object position
        # No collision with robot so safe to go close
        print("\n[3] Moving to object...")
        self.move_to(obj_pos, hand, tolerance=0.05)
        self._hold(100)
        # Grasp here — hand is at cube position
        self.grasp_object(obj_name, hand)
        self._hold(200)

        # Step 4 — GRASP (attach object)
        print("\n[4] Grasping...")
        self.grasp_object(obj_name, hand)
        self._hold(200)

        # Step 5 — lift WITH object
        print("\n[5] Lifting...")
        lift     = self.get_ee_pos(hand).copy()
        lift[2] += 0.15
        self.move_to(lift, hand)
        self._hold(200)

        # Verify object lifted
        obj_now = self.get_obj_pos(obj_name)
        print(f"   Object now at: {obj_now}")

        # Step 6 — place at Point B
        if place_pos is not None:
            print("\n[6] Moving to Point B...")
            pb      = np.array(place_pos,
                                dtype=float)
            above_b = pb.copy()
            above_b[2] += 0.10
            self.move_to(above_b, hand)
            self._hold(150)

            self.move_to(pb, hand,
                          tolerance=0.04)
            self._hold(200)

            # Step 7 — release
            print("\n[7] Releasing...")
            self.release_object()
            self._hold(800)  # settle on table

        # Step 8 — home
        print("\n[8] Going home...")
        self._go_home()
        print(f"\n✅ Done: {obj_name}!")
        return True

    def _go_home(self, steps=600):
        # Reset wrist roll
        import time
        wr_start = self.data.ctrl[26]
        for s in range(60):
            a = s / 60
            self.data.ctrl[26] = wr_start + a * (0.0 - wr_start)
            mujoco.mj_step(self.model, self.data)
            if self.viewer and self.viewer.is_running():
                self.viewer.sync()
            time.sleep(0.002)
        self.smooth_wrist(
            pitch=0.0, roll=0.0, yaw=0.0,
            steps=40)
        start  = self.data.ctrl.copy()
        target = np.zeros(self.model.nu)
        for i in range(steps):
            a = i/steps
            a = a*a*(3-2*a)
            self.data.ctrl[:] = (
                start + a*(target-start))
            if self.grasped:
                self._carry_object()
            mujoco.mj_step(self.model, self.data)
            if self.viewer.is_running():
                self.viewer.sync()
            time.sleep(0.002)

    def _hold(self, steps=200):
        for _ in range(steps):
            if self.grasped:
                self._carry_object()
            mujoco.mj_step(self.model, self.data)
            if self.viewer.is_running():
                self.viewer.sync()
            time.sleep(0.002)
