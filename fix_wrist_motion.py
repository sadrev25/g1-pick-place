with open('ik_controller.py', 'r') as f:
    content = f.read()

# Add wrist control method after __init__
OLD = '    def select_hand(self, obj_pos):'

NEW = '''    def set_wrist(self, pitch=0.0,
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
            if self.viewer and \
               self.viewer.is_running():
                self.viewer.sync()
            import time
            time.sleep(0.002)

    def select_hand(self, obj_pos):'''

if OLD in content:
    content = content.replace(OLD, NEW)
    print("Wrist methods added!")
else:
    print("Pattern not found!")

# Now fix pick_sequence to use wrist motion
OLD_SEQ = '''        # Step 1 — move directly above cube
        print("\\n[1] Moving above object...")
        above     = obj_pos.copy()
        above[2] += 0.12
        ok = self.move_to(above, hand,
                          tolerance=0.04)
        if not ok:
            print("❌ Cannot reach above!")
            self._go_home()
            return False
        self._hold(100)

        # Step 2 — move down to cube
        print("\\n[2] Moving to cube...")
        wrist_target = obj_pos.copy()
        wrist_target[0] -= 0.083
        self.move_to(wrist_target, hand,
                     tolerance=0.04)
        self._hold(100)

        # Step 3 — close gripper (teleport)
        print("\\n[3] Closing gripper...")
        self.grasp_object(obj_name, hand)
        self._hold(150)

        # Step 4 — lift straight up
        print("\\n[4] Lifting...")'''

NEW_SEQ = '''        # Step 1 — rotate wrist DOWN first
        # palm faces table = natural picking pose
        print("\\n[1] Preparing wrist...")
        self.smooth_wrist(
            pitch=-1.2,   # palm faces down
            roll=0.0,
            yaw=0.0,
            hand=hand, steps=60)

        # Step 2 — move above cube
        print("\\n[2] Moving above object...")
        above     = obj_pos.copy()
        above[2] += 0.12
        ok = self.move_to(above, hand,
                          tolerance=0.04)
        if not ok:
            print("❌ Cannot reach above!")
            self._go_home()
            return False
        self._hold(80)

        # Step 3 — move down to cube
        # palm still facing down
        print("\\n[3] Moving down to cube...")
        wrist_target = obj_pos.copy()
        wrist_target[0] -= 0.083
        self.move_to(wrist_target, hand,
                     tolerance=0.04)
        self._hold(80)

        # Step 4 — close gripper (teleport)
        print("\\n[4] Closing gripper...")
        self.grasp_object(obj_name, hand)
        self._hold(100)

        # Step 5 — rotate wrist to carry pose
        # palm faces inward = natural carry
        print("\\n[4b] Adjusting wrist...")
        self.smooth_wrist(
            pitch=-0.5,   # slight downward
            roll=0.0,
            yaw=0.0,
            hand=hand, steps=40)

        # Step 6 — lift straight up
        print("\\n[5] Lifting...")'''

if OLD_SEQ in content:
    content = content.replace(OLD_SEQ, NEW_SEQ)
    print("Pick sequence updated!")
else:
    print("Pick sequence pattern not found!")
    # Try to find it
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'Moving above' in line:
            print(f"  Found at line {i+1}: {line}")

# Fix go_home to reset wrist too
OLD_HOME = '''    def _go_home(self, steps=600):
        start  = self.data.ctrl.copy()
        target = np.zeros(self.model.nu)'''

NEW_HOME = '''    def _go_home(self, steps=600):
        # Reset wrist first
        self.smooth_wrist(
            pitch=0.0, roll=0.0, yaw=0.0,
            steps=40)
        start  = self.data.ctrl.copy()
        target = np.zeros(self.model.nu)'''

if OLD_HOME in content:
    content = content.replace(OLD_HOME, NEW_HOME)
    print("Go home wrist reset added!")

with open('ik_controller.py', 'w') as f:
    f.write(content)

import ast
try:
    ast.parse(content)
    print("Syntax OK!")
except SyntaxError as e:
    print(f"Error line {e.lineno}: {e.msg}")
