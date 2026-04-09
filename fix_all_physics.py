import re, ast

# ── Fix body.py ──────────────────────────────
with open('body.py', 'r') as f:
    body = f.read()

# Strategy:
# Floor/ground = contype=1 conaffinity=1 (default)
# Table        = contype=1 conaffinity=1 (sits on floor, catches cubes)
# Objects      = contype=1 conaffinity=1 (collide with table+floor)
# Robot arm    = contype=3 conaffinity=0 (no collision with anything)
# This way: cubes sit on table, robot arm passes through cubes

# Fix ALL object contype back to 1
# but make them heavier so they don't roll
NEW_OBJECTS = '''    objects = """
    <body name="table" pos="0.350 -0.149 0.820">
      <geom type="box" size="0.20 0.18 0.01"
            rgba="0.6 0.4 0.2 1" mass="100"
            contype="1" conaffinity="1"
            friction="2.0 0.1 0.1"/>
      <inertial pos="0 0 0" mass="100"
                diaginertia="10 10 10"/>
    </body>
    <body name="red_cube" pos="0.350 -0.149 0.875">
      <joint type="free"/>
      <geom type="box" size="0.04 0.04 0.04"
            rgba="0.9 0.2 0.2 1" mass="1.0"
            contype="1" conaffinity="1"
            friction="2.0 0.1 0.1"/>
      <inertial pos="0 0 0" mass="1.0"
                diaginertia="0.01 0.01 0.01"/>
    </body>
    <body name="blue_cube" pos="0.350 -0.030 0.875">
      <joint type="free"/>
      <geom type="box" size="0.035 0.035 0.035"
            rgba="0.2 0.2 0.9 1" mass="1.0"
            contype="1" conaffinity="1"
            friction="2.0 0.1 0.1"/>
      <inertial pos="0 0 0" mass="1.0"
                diaginertia="0.01 0.01 0.01"/>
    </body>
    <body name="green_cylinder" pos="0.350 -0.290 0.875">
      <joint type="free"/>
      <geom type="cylinder" size="0.035 0.04"
            rgba="0.2 0.8 0.2 1" mass="1.0"
            contype="1" conaffinity="1"
            friction="2.0 0.1 0.1"/>
      <inertial pos="0 0 0" mass="1.0"
                diaginertia="0.01 0.01 0.01"/>
    </body>
    <body name="container" pos="0.130 -0.299 0.831">
      <geom type="box" size="0.10 0.10 0.01"
            rgba="0.3 0.3 0.3 1" mass="100"
            contype="1" conaffinity="1"
            friction="2.0 0.1 0.1"/>
      <inertial pos="0 0 0" mass="100"
                diaginertia="10 10 10"/>
    </body>
"""'''

# Replace entire objects block
body = re.sub(
    r'objects = """.*?"""',
    NEW_OBJECTS,
    body, flags=re.DOTALL)

# Now disable robot arm collision
# Add this right after g1_fixed.xml is written
DISABLE_ARM = '''
    # Disable arm collision so hand passes through objects
    # This lets teleport grasp work without pushing
    os.chdir(g1_dir)
    model_tmp = mujoco.MjModel.from_xml_string(scene)
    os.chdir(os.path.expanduser('~'))
'''

with open('body.py', 'w') as f:
    f.write(body)
print("✅ body.py physics fixed!")

# ── Fix ik_controller.py ─────────────────────
with open('ik_controller.py', 'r') as f:
    ik = f.read()

# After model loads, disable arm geom collision
# We do this by patching _load in RobotBody
# Actually easier: patch IKController.__init__
# to set arm geom contype=0 after load

OLD_INIT_END = '''        mujoco.mj_forward(model, data)
        print(f"✅ IK ready!")
        print(f"   R wrist: "
              f"{data.xpos[self.r_wrist]}")'''

NEW_INIT_END = '''        # Disable collision on arm geoms
        # So hand passes through objects cleanly
        # Teleport grasp handles pick instead
        arm_bodies = [
            'right_shoulder_pitch_link',
            'right_shoulder_roll_link',
            'right_shoulder_yaw_link',
            'right_elbow_link',
            'right_wrist_roll_link',
            'right_wrist_pitch_link',
            'right_wrist_yaw_link',
            'left_shoulder_pitch_link',
            'left_shoulder_roll_link',
            'left_shoulder_yaw_link',
            'left_elbow_link',
            'left_wrist_roll_link',
            'left_wrist_pitch_link',
            'left_wrist_yaw_link',
        ]
        for i in range(model.ngeom):
            bid   = model.geom_bodyid[i]
            bname = model.body(bid).name
            if bname in arm_bodies:
                model.geom_contype[i]     = 0
                model.geom_conaffinity[i] = 0

        mujoco.mj_forward(model, data)
        print(f"✅ IK ready — arm collision disabled!")
        print(f"   R wrist: "
              f"{data.xpos[self.r_wrist]}")'''

if OLD_INIT_END in ik:
    ik = ik.replace(OLD_INIT_END, NEW_INIT_END)
    print("✅ Arm collision disabled in IK init!")
else:
    # Fallback — find mj_forward near IK ready
    ik = ik.replace(
        'print(f"✅ IK ready!")',
        '''# Disable arm geom collision
        arm_bodies = [
            'right_shoulder_pitch_link','right_shoulder_roll_link',
            'right_shoulder_yaw_link','right_elbow_link',
            'right_wrist_roll_link','right_wrist_pitch_link',
            'right_wrist_yaw_link',
            'left_shoulder_pitch_link','left_shoulder_roll_link',
            'left_shoulder_yaw_link','left_elbow_link',
            'left_wrist_roll_link','left_wrist_pitch_link',
            'left_wrist_yaw_link',
        ]
        for i in range(model.ngeom):
            bid = model.geom_bodyid[i]
            if model.body(bid).name in arm_bodies:
                model.geom_contype[i]     = 0
                model.geom_conaffinity[i] = 0
        print(f"✅ IK ready — arm collision disabled!")''')
    print("✅ Fallback arm collision fix applied!")

# Fix place — drop cube right at table surface
ik = re.sub(
    r'place_target\[2\] = pb\[2\] \+ 0\.05',
    'place_target[2] = pb[2] + 0.02',
    ik)

with open('ik_controller.py', 'w') as f:
    f.write(ik)
print("✅ ik_controller.py updated!")

# Fix POINT_B to match new table/container pos
with open('main.py', 'r') as f:
    main = f.read()
main = re.sub(
    r'POINT_B\s*=\s*\[.*?\]',
    'POINT_B = [0.130, -0.299, 0.841]',
    main)
with open('main.py', 'w') as f:
    f.write(main)
print("✅ POINT_B updated!")

# Verify syntax
print("\n=== SYNTAX CHECK ===")
for fname in ['body.py', 'ik_controller.py', 'main.py']:
    with open(fname) as f:
        src = f.read()
    try:
        ast.parse(src)
        print(f"✅ {fname}")
    except SyntaxError as e:
        print(f"❌ {fname} line {e.lineno}: {e.msg}")
