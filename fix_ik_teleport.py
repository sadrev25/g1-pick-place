import re

with open('ik_controller.py', 'r') as f:
    content = f.read()

print("=== CURRENT GRASP THRESHOLD ===")
# Find grasp threshold
matches = re.findall(
    r'(tolerance|threshold|dist|err|gap)\s*[<>=]+\s*([\d.]+)',
    content)
for m in matches:
    print(f"  {m[0]} compare {m[1]}")

print("\n=== MOVE_TO FUNCTION ===")
# Find move_to or similar
lines = content.split('\n')
for i, line in enumerate(lines):
    if any(x in line.lower() for x in
           ['def move', 'def pick', 'def grasp',
            'teleport', 'attach', 'tolerance',
            'threshold', 'grasped']):
        print(f"  {i+1}: {line}")
