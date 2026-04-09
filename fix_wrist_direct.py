with open('ik_controller.py', 'r') as f:
    lines = f.readlines()

# Wrist rotation code to insert
# Goes before line 345 (index 344)
wrist_code = '''        # Step 0 — rotate wrist DOWN
        # pitch=-1.2 = palm faces table
        import time
        print("\\n[0] Rotating wrist down...")
        wp_start = self.data.ctrl[27]
        wr_start = self.data.ctrl[26]
        for s in range(80):
            a = s / 80
            a = a * a * (3 - 2 * a)
            self.data.ctrl[27] = (
                wp_start +
                a * (-1.2 - wp_start))
            self.data.ctrl[26] = (
                wr_start +
                a * (0.0 - wr_start))
            mujoco.mj_step(
                self.model, self.data)
            if self.viewer and \\
               self.viewer.is_running():
                self.viewer.sync()
            time.sleep(0.002)
        print("   Palm down!")

        # Compute IK target accounting for palm
        bid      = (self.r_wrist
                    if hand == 'right'
                    else self.l_wrist)
        mujoco.mj_forward(
            self.model, self.data)
        mat      = self.data.xmat[
            bid].reshape(3, 3)
        palm_dir = mat[:, 0]
        palm_off = palm_dir * 0.058

'''

# Find the line with "Step 1 — above object"
insert_idx = None
for i, line in enumerate(lines):
    if '# Step 1' in line and 'above object' in line:
        insert_idx = i
        print(f"Found Step 1 at line {i+1}")
        break

if insert_idx is None:
    print("Not found! Searching nearby...")
    for i, line in enumerate(lines):
        if 'Moving above object' in line:
            insert_idx = i - 1
            print(f"Found via print at line {i+1}")
            break

if insert_idx:
    lines.insert(insert_idx,
                 wrist_code)
    print(f"Inserted wrist code at line {insert_idx+1}")

    # Also fix Step 1 target to use palm offset
    # Find "above[2] += 0.10" and fix IK target
    for i, line in enumerate(lines):
        if 'above[2] += 0.10' in line:
            # Add palm offset correction after
            lines[i] = line
            lines.insert(i+1,
                '        ik_above = above - palm_off\n')
            break

    # Fix move_to call to use ik_above
    for i, line in enumerate(lines):
        if 'ok = self.move_to(above, hand)' in line:
            lines[i] = line.replace(
                'self.move_to(above, hand)',
                'self.move_to(ik_above, hand)')
            print("Fixed move_to target!")
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
else:
    print("❌ Could not find insertion point!")
