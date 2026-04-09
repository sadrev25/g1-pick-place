import re

# Fix 1: palm offset in _carry_object
# Currently offset is [0.05, 0, 0] = forearm level
# Need bigger offset so cube appears in PALM
with open('ik_controller.py', 'r') as f:
    ik = f.read()

# Increase palm offset so cube is further from wrist
# G1 forearm length ~0.15m so palm is ~0.18m from wrist
ik = ik.replace(
    'palm_offset = np.array([0.05, 0.0, 0.0])',
    'palm_offset = np.array([0.18, 0.0, 0.0])')

with open('ik_controller.py', 'w') as f:
    f.write(ik)
print("✅ Palm offset updated to 0.18m")

# Fix 2: spread objects further apart
# Currently red and green are only 0.07m apart = touching
# Need at least 0.12m gap
with open('body.py', 'r') as f:
    body = f.read()

# Spread objects more — wider Y spacing
body = body.replace(
    'pos="0.350 -0.149 0.870"',   # red — keep center
    'pos="0.350 -0.149 0.870"')

body = body.replace(
    'pos="0.350 -0.079 0.870"',   # blue — move left
    'pos="0.350 -0.049 0.870"')

body = body.replace(
    'pos="0.350 -0.219 0.880"',   # green — move right
    'pos="0.350 -0.269 0.880"')

with open('body.py', 'w') as f:
    f.write(body)
print("✅ Objects spread apart")

# Verify spacing
import numpy as np
red   = np.array([0.350, -0.149, 0.870])
blue  = np.array([0.350, -0.049, 0.870])
green = np.array([0.350, -0.269, 0.880])

print(f"\nObject spacing:")
print(f"  red-blue:  {np.linalg.norm(red-blue):.3f}m")
print(f"  red-green: {np.linalg.norm(red-green):.3f}m")
print(f"  (need >0.10m to not touch)")
