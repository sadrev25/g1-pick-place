with open('ik_controller.py', 'r') as f:
    content = f.read()

# Fix __init__ to verify wrist ID found correctly
OLD = '''        self.r_wrist = mujoco.mj_name2id(
            model, mujoco.mjtObj.mjOBJ_BODY,
            'right_wrist_yaw_link')
        self.l_wrist = mujoco.mj_name2id(
            model, mujoco.mjtObj.mjOBJ_BODY,
            'left_wrist_yaw_link')'''

NEW = '''        self.r_wrist = mujoco.mj_name2id(
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
              f"pos={data.xpos[self.l_wrist]}")'''

import ast
if OLD in content:
    content = content.replace(OLD, NEW)
    print("✅ Fixed wrist init")
else:
    print("❌ Pattern not found")
    # Just add assert after existing lookup
    content = content.replace(
        "mujoco.mj_forward(model, data)\n        print(f\"✅ IK ready!\")",
        "mujoco.mj_forward(model, data)\n"
        "        assert self.r_wrist >= 0, 'right_wrist_yaw_link not found!'\n"
        "        assert self.l_wrist >= 0, 'left_wrist_yaw_link not found!'\n"
        "        print(f'✅ IK ready!')\n"
        "        print(f'   R wrist ID={self.r_wrist} pos={data.xpos[self.r_wrist]}')")
    print("✅ Applied fallback fix")

with open('ik_controller.py', 'w') as f:
    f.write(content)

try:
    ast.parse(content)
    print("✅ Syntax OK")
except SyntaxError as e:
    print(f"❌ Line {e.lineno}: {e.msg}")
