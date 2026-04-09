import re, ast

# ── 1. Fix body.py — add walled container ──
with open('body.py', 'r') as f:
    body = f.read()

# Replace flat container with walled box
OLD_CONTAINER = '''    <body name="container" pos="0.130 -0.299 0.831">
      <geom type="box" size="0.10 0.10 0.01"
            rgba="0.3 0.3 0.3 1" mass="100"
            contype="1" conaffinity="1"
            friction="2.0 0.1 0.1"/>
      <inertial pos="0 0 0" mass="100"
                diaginertia="10 10 10"/>
    </body>'''

NEW_CONTAINER = '''    <body name="container" pos="0.130 -0.299 0.831">
      <!-- floor of container -->
      <geom name="cont_floor"
            type="box" size="0.08 0.08 0.008"
            pos="0 0 0"
            rgba="0.3 0.3 0.3 1" mass="50"
            contype="1" conaffinity="1"
            friction="2.0 0.1 0.1"/>
      <!-- front wall -->
      <geom name="cont_front"
            type="box" size="0.08 0.008 0.04"
            pos="0 -0.088 0.04"
            rgba="0.3 0.3 0.3 0.6"
            contype="1" conaffinity="1"/>
      <!-- back wall -->
      <geom name="cont_back"
            type="box" size="0.08 0.008 0.04"
            pos="0 0.088 0.04"
            rgba="0.3 0.3 0.3 0.6"
            contype="1" conaffinity="1"/>
      <!-- left wall -->
      <geom name="cont_left"
            type="box" size="0.008 0.08 0.04"
            pos="-0.088 0 0.04"
            rgba="0.3 0.3 0.3 0.6"
            contype="1" conaffinity="1"/>
      <!-- right wall -->
      <geom name="cont_right"
            type="box" size="0.008 0.08 0.04"
            pos="0.088 0 0.04"
            rgba="0.3 0.3 0.3 0.6"
            contype="1" conaffinity="1"/>
      <inertial pos="0 0 0" mass="50"
                diaginertia="1 1 1"/>
    </body>'''

if OLD_CONTAINER in body:
    body = body.replace(OLD_CONTAINER, NEW_CONTAINER)
    print("✅ Container replaced with walled box!")
else:
    # Regex fallback
    body = re.sub(
        r'<body name="container".*?</body>',
        NEW_CONTAINER,
        body, flags=re.DOTALL)
    print("✅ Container replaced via regex!")

with open('body.py', 'w') as f:
    f.write(body)

# ── 2. Fix POINT_B — must be INSIDE container ──
# Container pos = [0.130, -0.299, 0.831]
# Container floor top = 0.831 + 0.008 = 0.839
# Drop cube at 0.839 + 0.05 = 0.889 (above floor)
with open('main.py', 'r') as f:
    main = f.read()
main = re.sub(
    r'POINT_B\s*=\s*\[.*?\]',
    'POINT_B = [0.130, -0.299, 0.889]',
    main)
with open('main.py', 'w') as f:
    f.write(main)
print("✅ POINT_B set to inside container!")

# ── 3. Fix release — drop slowly, wait to settle ──
with open('ik_controller.py', 'r') as f:
    ik = f.read()

# Extend settle time after release
ik = re.sub(
    r'self\.release_object\(\)\s*\n\s*self\._hold\(\d+\)',
    'self.release_object()\n            self._hold(800)',
    ik)
print("✅ Release settle time extended!")

with open('ik_controller.py', 'w') as f:
    f.write(ik)

# ── 4. Syntax check all files ──
print("\n=== SYNTAX CHECK ===")
for fname in ['body.py', 'ik_controller.py', 'main.py']:
    with open(fname) as f:
        src = f.read()
    try:
        ast.parse(src)
        print(f"✅ {fname}")
    except SyntaxError as e:
        print(f"❌ {fname} line {e.lineno}: {e.msg}")
        lines = src.split('\n')
        for j in range(max(0,e.lineno-2),
                       min(len(lines),e.lineno+2)):
            print(f"   {j+1}: {repr(lines[j])}")
