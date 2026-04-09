with open('ik_controller.py', 'r') as f:
    content = f.read()

# Fix: move TO place position first, THEN release
# Currently releases while still above (above_b)
OLD = '''            print("\\n[6] Moving to Point B...")
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
            print("\\n[7] Releasing...")
            self.release_object()
            self._hold(300)'''

NEW = '''            print("\\n[6] Moving to Point B...")
            pb      = np.array(place_pos,
                                dtype=float)
            # Move above first
            above_b = pb.copy()
            above_b[2] += 0.12
            self.move_to(above_b, hand)
            self._hold(150)
            # Move down to just above table surface
            # pb[2] = table surface + small gap
            place_target = pb.copy()
            place_target[2] = pb[2] + 0.05
            self.move_to(place_target, hand,
                          tolerance=0.04)
            self._hold(200)
            # Step 7 — release RIGHT above table
            print("\\n[7] Releasing...")
            self.release_object()
            # Let physics settle cube onto table
            self._hold(500)'''

if OLD in content:
    content = content.replace(OLD, NEW)
    print("✅ Place sequence fixed!")
else:
    print("❌ Pattern not found — trying regex")
    import re
    content = re.sub(
        r'self\.release_object\(\)\s*\n\s*self\._hold\(\d+\)',
        'self.release_object()\n            self._hold(500)  # settle on table',
        content)
    print("✅ Release hold extended!")

with open('ik_controller.py', 'w') as f:
    f.write(content)

# Also fix POINT_B z height in main.py
# Should be table surface = 0.851
with open('main.py', 'r') as f:
    main = f.read()

import re
# Print current POINT_B
match = re.search(r'POINT_B\s*=\s*\[([^\]]+)\]', main)
if match:
    print(f"Current POINT_B: [{match.group(1)}]")

# Fix z to be table surface height
main = re.sub(
    r'POINT_B\s*=\s*\[([^\]]+)\]',
    'POINT_B = [0.130, -0.299, 0.860]',
    main)
with open('main.py', 'w') as f:
    f.write(main)
print("✅ POINT_B z fixed to table surface!")

import ast
for fname in ['ik_controller.py', 'main.py']:
    with open(fname) as f:
        src = f.read()
    try:
        ast.parse(src)
        print(f"✅ {fname} OK")
    except SyntaxError as e:
        print(f"❌ {fname} line {e.lineno}: {e.msg}")
