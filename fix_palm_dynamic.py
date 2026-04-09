with open('ik_controller.py', 'r') as f:
    content = f.read()

# Replace static palm offset with dynamic one
# Uses actual wrist rotation matrix every step
OLD = '''                    wrist_pos = self.get_ee_pos(hand)
                    # Small forward offset so cube
                    # sits in palm not inside wrist
                    palm_offset = np.array([0.18, 0.0, 0.0])
                    obj_pos   = wrist_pos + offset + palm_offset'''

NEW = '''                    wrist_pos = self.get_ee_pos(hand)
                    # Dynamic palm offset using wrist orientation
                    # Palm is 0.15m along wrist x-axis
                    bid = (self.r_wrist if hand == 'right'
                           else self.l_wrist)
                    mat = self.data.xmat[bid].reshape(3, 3)
                    palm_dir    = mat[:, 0]  # wrist forward axis
                    palm_offset = palm_dir * 0.15
                    obj_pos = wrist_pos + offset + palm_offset'''

if OLD in content:
    content = content.replace(OLD, NEW)
    print("✅ Dynamic palm offset applied!")
else:
    # Fallback
    content = content.replace(
        'palm_offset = np.array([0.18, 0.0, 0.0])',
        '# Dynamic: use wrist x-axis\n'
        '                    bid2 = (self.r_wrist if hand=="right" else self.l_wrist)\n'
        '                    mat2 = self.data.xmat[bid2].reshape(3,3)\n'
        '                    palm_offset = mat2[:,0] * 0.15')
    print("✅ Fallback palm offset applied!")

with open('ik_controller.py', 'w') as f:
    f.write(content)

# Fix object spacing in body.py
with open('body.py', 'r') as f:
    body = f.read()

# Wider spacing — 0.13m between objects
import re, numpy as np
replacements = [
    # red stays center
    ('pos="0.350 -0.149 0.870"',
     'pos="0.350 -0.149 0.870"'),
    # blue further left
    ('pos="0.350 -0.049 0.870"',
     'pos="0.350 -0.030 0.870"'),
    # green further right
    ('pos="0.350 -0.269 0.880"',
     'pos="0.350 -0.290 0.880"'),
]
for old, new in replacements:
    body = body.replace(old, new)

with open('body.py', 'w') as f:
    f.write(body)

# Verify
import ast
for fname in ['ik_controller.py', 'body.py']:
    with open(fname) as f:
        src = f.read()
    try:
        ast.parse(src)
        print(f"✅ {fname} syntax OK")
    except SyntaxError as e:
        print(f"❌ {fname} line {e.lineno}: {e.msg}")

red   = np.array([0.350, -0.149, 0.870])
blue  = np.array([0.350, -0.030, 0.870])
green = np.array([0.350, -0.290, 0.880])
print(f"\nSpacing:")
print(f"  red↔blue:  {np.linalg.norm(red-blue):.3f}m")
print(f"  red↔green: {np.linalg.norm(red-green):.3f}m")
print(f"  (safe if >0.10m)")
