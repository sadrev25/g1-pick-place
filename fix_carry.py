with open('ik_controller.py', 'r') as f:
    content = f.read()

# Fix 1: _carry_object — add small forward offset
# so cube appears IN the hand not inside the wrist
OLD_CARRY = '''                    wrist_pos = self.get_ee_pos(hand)
                    obj_pos   = wrist_pos + offset'''

NEW_CARRY = '''                    wrist_pos = self.get_ee_pos(hand)
                    # Small forward offset so cube
                    # sits in palm not inside wrist
                    palm_offset = np.array([0.05, 0.0, 0.0])
                    obj_pos   = wrist_pos + offset + palm_offset'''

# Fix 2: grasp_object — print actual gap for debug
OLD_GRASP = '''        # Zero offset — cube snaps to wrist
        # This prevents floating during carry
        offset = np.zeros(3)
        self.grasped = (obj_name, hand, offset)

        # Immediately teleport cube to wrist
        self._carry_object()
        print(f"   Grasped {obj_name}! "
              f"snapped to wrist.")'''

NEW_GRASP = '''        # Zero offset — cube snaps to palm
        offset = np.zeros(3)
        self.grasped = (obj_name, hand, offset)

        # Immediately teleport cube to hand
        self._carry_object()
        # Verify it worked
        new_obj = self.get_obj_pos(obj_name)
        new_wrist = self.get_ee_pos(hand)
        actual_gap = np.linalg.norm(new_obj - new_wrist)
        print(f"   Grasped {obj_name}!")
        print(f"   Wrist:  {new_wrist}")
        print(f"   Cube:   {new_obj}")
        print(f"   Gap:    {actual_gap:.3f}m")'''

fixed = content
if OLD_CARRY in fixed:
    fixed = fixed.replace(OLD_CARRY, NEW_CARRY)
    print("✅ Fixed carry offset")
else:
    print("❌ carry pattern not found — manual fix")
    import re
    fixed = re.sub(
        r'obj_pos\s*=\s*wrist_pos \+ offset',
        'obj_pos = wrist_pos + offset + np.array([0.05, 0.0, 0.0])',
        fixed)
    print("✅ Applied regex carry fix")

if OLD_GRASP in fixed:
    fixed = fixed.replace(OLD_GRASP, NEW_GRASP)
    print("✅ Fixed grasp debug output")
else:
    print("⚠️  grasp pattern not found — skipping")

with open('ik_controller.py', 'w') as f:
    f.write(fixed)

# Verify syntax
import ast
try:
    ast.parse(fixed)
    print("✅ Syntax OK")
except SyntaxError as e:
    print(f"❌ Syntax error line {e.lineno}: {e.msg}")
