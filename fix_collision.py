import re

with open('body.py', 'r') as f:
    content = f.read()

# Objects should NOT collide with robot arm
# contype=1 conaffinity=2 = collides with floor(2) not robot(1)
# Robot arm geoms are contype=1 conaffinity=1
# Floor is contype=2 conaffinity=2

OLD_OBJECTS = '''    objects = """
    <body name="table" pos="0.230 -0.149 0.840">
      <geom type="box" size="0.15 0.12 0.01"
            rgba="0.6 0.4 0.2 1" mass="20"
            contype="1" conaffinity="1"/>
      <inertial pos="0 0 0" mass="20"
                diaginertia="1 1 1"/>
    </body>
    <body name="red_cube" pos="0.230 -0.149 0.890">
      <joint type="free"/>
      <geom type="box" size="0.04 0.04 0.04"
            rgba="0.9 0.2 0.2 1" mass="0.3"
            contype="1" conaffinity="1"/>
      <inertial pos="0 0 0" mass="0.3"
                diaginertia="0.001 0.001 0.001"/>
    </body>
    <body name="blue_cube" pos="0.230 -0.079 0.890">
      <joint type="free"/>
      <geom type="box" size="0.025 0.025 0.025"
            rgba="0.2 0.2 0.9 1" mass="0.1"
            contype="1" conaffinity="1"/>
      <inertial pos="0 0 0" mass="0.1"
                diaginertia="0.0005 0.0005 0.0005"/>
    </body>
    <body name="green_cylinder" pos="0.230 -0.219 0.900">
      <joint type="free"/>
      <geom type="cylinder" size="0.03 0.05"
            rgba="0.2 0.8 0.2 1" mass="0.2"
            contype="1" conaffinity="1"/>
      <inertial pos="0 0 0" mass="0.2"
                diaginertia="0.001 0.001 0.001"/>
    </body>
    <body name="container" pos="0.130 -0.299 0.851">
      <geom type="box" size="0.10 0.10 0.01"
            rgba="0.3 0.3 0.3 1" mass="5"
            contype="1" conaffinity="1"/>
      <inertial pos="0 0 0" mass="5"
                diaginertia="1 1 1"/>
    </body>
"""'''

NEW_OBJECTS = '''    objects = """
    <body name="table" pos="0.230 -0.149 0.840">
      <geom type="box" size="0.15 0.12 0.01"
            rgba="0.6 0.4 0.2 1" mass="20"
            contype="2" conaffinity="2"/>
      <inertial pos="0 0 0" mass="20"
                diaginertia="1 1 1"/>
    </body>
    <body name="red_cube" pos="0.230 -0.149 0.890">
      <joint type="free"/>
      <geom type="box" size="0.04 0.04 0.04"
            rgba="0.9 0.2 0.2 1" mass="0.3"
            contype="2" conaffinity="2"/>
      <inertial pos="0 0 0" mass="0.3"
                diaginertia="0.001 0.001 0.001"/>
    </body>
    <body name="blue_cube" pos="0.230 -0.079 0.890">
      <joint type="free"/>
      <geom type="box" size="0.025 0.025 0.025"
            rgba="0.2 0.2 0.9 1" mass="0.1"
            contype="2" conaffinity="2"/>
      <inertial pos="0 0 0" mass="0.1"
                diaginertia="0.0005 0.0005 0.0005"/>
    </body>
    <body name="green_cylinder" pos="0.230 -0.219 0.900">
      <joint type="free"/>
      <geom type="cylinder" size="0.03 0.05"
            rgba="0.2 0.8 0.2 1" mass="0.2"
            contype="2" conaffinity="2"/>
      <inertial pos="0 0 0" mass="0.2"
                diaginertia="0.001 0.001 0.001"/>
    </body>
    <body name="container" pos="0.130 -0.299 0.851">
      <geom type="box" size="0.10 0.10 0.01"
            rgba="0.3 0.3 0.3 1" mass="5"
            contype="2" conaffinity="2"/>
      <inertial pos="0 0 0" mass="5"
                diaginertia="1 1 1"/>
    </body>
"""'''

if OLD_OBJECTS in content:
    content = content.replace(OLD_OBJECTS, NEW_OBJECTS)
    print("✅ Object collision disabled vs robot!")
else:
    # Fallback — just regex replace all contype/affinity in objects
    content = re.sub(
        r'(contype|conaffinity)="1"',
        r'\1="2"',
        content)
    print("✅ Applied regex collision fix")

with open('body.py', 'w') as f:
    f.write(content)

import ast
with open('ik_controller.py') as f:
    ik = f.read()

# Fix pick_sequence step 3 — grasp EXACTLY
# at object position not 0.06 above
OLD_STEP3 = '''        # Step 3 — GRASP before touching
        # Stay above, teleport grasp fires here
        print("\\n[3] Grasping from above...")
        align    = obj_pos.copy()
        align[2] = obj_pos[2] + 0.06
        self.move_to(align, hand, tolerance=0.03)
        self._hold(100)
        self.grasp_object(obj_name, hand)
        self._hold(200)'''

NEW_STEP3 = '''        # Step 3 — move to EXACT object position
        # No collision with robot so safe to go close
        print("\\n[3] Moving to object...")
        self.move_to(obj_pos, hand, tolerance=0.05)
        self._hold(100)
        # Grasp here — hand is at cube position
        self.grasp_object(obj_name, hand)
        self._hold(200)'''

if OLD_STEP3 in ik:
    ik = ik.replace(OLD_STEP3, NEW_STEP3)
    print("✅ Fixed step 3 grasp position")
else:
    print("⚠️  step3 pattern not found — check manually")

with open('ik_controller.py', 'w') as f:
    f.write(ik)

print("\nDone! Run: python3 main.py")
