with open('ik_controller.py', 'r') as f:
    content = f.read()

OLD = '''        # Step 1 — above object
        print("\\n[1] Moving above object...")
        above     = obj_pos.copy()
        above[2] += 0.10
        ok = self.move_to(above, hand)
        if not ok:
            print("❌ Cannot reach!")
            self._go_home()
            return False
        self._hold(150)
        # Step 2 — align XY with object
        print("\\n[2] Aligning...")
        align    = obj_pos.copy()
        align[2] = self.get_ee_pos(hand)[2]
        self.move_to(align, hand, tolerance=0.02)
        self._hold(150)
        # Step 3 — move to EXACT object position
        # No collision with robot so safe to go close
        print("\\n[3] Moving to object...")
        self.move_to(obj_pos, hand, tolerance=0.05)
        self._hold(100)
        # Grasp here — hand is at cube position
        self.grasp_object(obj_name, hand)
        self._hold(200)
        # Step 4 — GRASP (attach object)
        print("\\n[4] Grasping...")
        self.grasp_object(obj_name, hand)
        self._hold(200)'''

NEW = '''        # Step 0 — rotate wrist DOWN
        # palm faces table before approaching
        print("\\n[0] Rotating wrist down...")
        import time
        wp_start = self.data.ctrl[27]
        wr_start = self.data.ctrl[26]
        for s in range(80):
            a = s / 80
            a = a * a * (3 - 2 * a)
            self.data.ctrl[27] = (
                wp_start + a * (-1.2 - wp_start))
            self.data.ctrl[26] = (
                wr_start + a * (0.0 - wr_start))
            mujoco.mj_step(self.model, self.data)
            if self.viewer and \
               self.viewer.is_running():
                self.viewer.sync()
            time.sleep(0.002)
        print("   Palm facing down!")

        # Compute palm offset — wrist to palm tip
        # Palm is 0.058m along wrist x-axis
        # So IK target = obj_pos - palm_offset
        # This puts palm EXACTLY at cube
        bid = (self.r_wrist if hand == 'right'
               else self.l_wrist)
        mujoco.mj_forward(self.model, self.data)
        mat        = self.data.xmat[bid].reshape(3,3)
        palm_dir   = mat[:, 0]
        palm_off   = palm_dir * 0.058

        # Step 1 — move above cube
        # IK target is shifted back by palm offset
        print("\\n[1] Moving above object...")
        above        = obj_pos.copy()
        above[2]    += 0.12
        ik_above     = above - palm_off
        ok = self.move_to(ik_above, hand)
        if not ok:
            print("❌ Cannot reach!")
            self._go_home()
            return False
        self._hold(100)

        # Step 2 — descend to cube
        # Palm will land exactly on cube
        print("\\n[2] Descending to cube...")
        ik_target = obj_pos - palm_off
        self.move_to(ik_target, hand,
                     tolerance=0.04)
        self._hold(100)

        # Step 3 — grasp
        print("\\n[3] Grasping...")
        self.grasp_object(obj_name, hand)
        self._hold(150)

        # Step 4 — rotate wrist to carry pose
        print("\\n[4] Carry pose...")
        wp_start = self.data.ctrl[27]
        for s in range(50):
            a = s / 50
            a = a * a * (3 - 2 * a)
            self.data.ctrl[27] = (
                wp_start + a * (-0.5 - wp_start))
            if self.grasped:
                self._carry_object()
            mujoco.mj_step(self.model, self.data)
            if self.viewer and \
               self.viewer.is_running():
                self.viewer.sync()
            time.sleep(0.002)'''

if OLD in content:
    content = content.replace(OLD, NEW)
    print("✅ Pick sequence fixed!")
else:
    print("❌ Pattern not found!")

# Fix palm offset in _carry_object to 0.058
content = content.replace(
    'palm_offset = palm_dir * 0.15',
    'palm_offset = palm_dir * 0.058')
content = content.replace(
    'palm_offset = palm_dir * 0.083',
    'palm_offset = palm_dir * 0.058')
print("✅ Palm offset set to 0.058m!")

with open('ik_controller.py', 'w') as f:
    f.write(content)

import ast
try:
    ast.parse(content)
    print("✅ Syntax OK!")
except SyntaxError as e:
    print(f"❌ line {e.lineno}: {e.msg}")
