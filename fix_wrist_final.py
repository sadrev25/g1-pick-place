with open('ik_controller.py', 'r') as f:
    lines = f.readlines()

# Find Step 0 wrist rotation we added before
# and replace with correct values
new_wrist = '''        # Step 0 — rotate wrist DOWN
        # ctrl[26] = wrist_roll = -1.97
        # This flips palm to face table
        import time
        print("\\n[0] Rotating wrist down...")
        wr_start = self.data.ctrl[26]
        for s in range(100):
            a = s / 100
            a = a * a * (3 - 2 * a)
            self.data.ctrl[26] = (
                wr_start +
                a * (-1.97 - wr_start))
            mujoco.mj_step(
                self.model, self.data)
            if self.viewer and \\
               self.viewer.is_running():
                self.viewer.sync()
            time.sleep(0.002)
        print("   Palm facing down!")

'''

# Find existing Step 0 and replace it
start_idx = None
end_idx   = None
for i, line in enumerate(lines):
    if '# Step 0' in line and 'wrist' in line.lower():
        start_idx = i
    if start_idx and '# Step 1' in line and 'above' in line:
        end_idx = i
        break

if start_idx and end_idx:
    lines[start_idx:end_idx] = [new_wrist]
    print(f"Replaced Step 0 lines {start_idx+1}"
          f" to {end_idx+1}")
else:
    print("Step 0 not found — inserting before Step 1")
    for i, line in enumerate(lines):
        if '# Step 1' in line and 'above' in line:
            lines.insert(i, new_wrist)
            print(f"Inserted at line {i+1}")
            break

# Fix go_home to reset wrist roll too
for i, line in enumerate(lines):
    if 'Reset wrist first' in line:
        # Replace the smooth_wrist call
        # with direct ctrl reset
        lines[i] = (
            '        # Reset wrist roll\n'
            '        import time\n'
            '        wr_start = '
            'self.data.ctrl[26]\n'
            '        for s in range(60):\n'
            '            a = s / 60\n'
            '            self.data.ctrl[26]'
            ' = wr_start + a * (0.0 - wr_start)\n'
            '            mujoco.mj_step('
            'self.model, self.data)\n'
            '            if self.viewer and'
            ' self.viewer.is_running():\n'
            '                '
            'self.viewer.sync()\n'
            '            time.sleep(0.002)\n')
        print("Fixed go_home wrist reset!")
        break

with open('ik_controller.py', 'w') as f:
    f.writelines(lines)

import ast
with open('ik_controller.py') as f:
    src = f.read()
try:
    ast.parse(src)
    print("✅ Syntax OK!")
except SyntaxError as e:
    print(f"❌ line {e.lineno}: {e.msg}")
    lines2 = src.split('\n')
    for j in range(max(0, e.lineno-3),
                   min(len(lines2), e.lineno+3)):
        print(f"  {j+1}: {repr(lines2[j])}")
