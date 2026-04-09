import re

# From your actual measurements:
# Wrist neutral: x=0.200, y=-0.149, z=0.888
# These are the correct positions

TABLE_X = 0.230
TABLE_Y = -0.149
TABLE_Z = 0.840   # just below wrist z=0.888

TABLE_SURFACE = TABLE_Z + 0.01   # 0.850
CUBE_Z        = TABLE_SURFACE + 0.04  # 0.890 = at wrist height

RED    = f"{TABLE_X:.3f} {TABLE_Y:.3f} {CUBE_Z:.3f}"
BLUE   = f"{TABLE_X:.3f} {TABLE_Y+0.07:.3f} {CUBE_Z:.3f}"
GREEN  = f"{TABLE_X:.3f} {TABLE_Y-0.07:.3f} {CUBE_Z+0.01:.3f}"
TABLE  = f"{TABLE_X:.3f} {TABLE_Y:.3f} {TABLE_Z:.3f}"
TARGET = f"{TABLE_X-0.10:.3f} {TABLE_Y-0.15:.3f} {TABLE_SURFACE:.3f}"

print(f"table:   {TABLE}")
print(f"red:     {RED}")
print(f"blue:    {BLUE}")
print(f"green:   {GREEN}")
print(f"target:  {TARGET}")

NEW_OBJECTS = f"""
    <body name="table" pos="{TABLE}">
      <geom type="box" size="0.15 0.12 0.01"
            rgba="0.6 0.4 0.2 1" mass="20"
            contype="1" conaffinity="1"/>
      <inertial pos="0 0 0" mass="20"
                diaginertia="1 1 1"/>
    </body>
    <body name="red_cube" pos="{RED}">
      <joint type="free"/>
      <geom type="box" size="0.04 0.04 0.04"
            rgba="0.9 0.2 0.2 1" mass="0.3"
            contype="1" conaffinity="1"/>
      <inertial pos="0 0 0" mass="0.3"
                diaginertia="0.001 0.001 0.001"/>
    </body>
    <body name="blue_cube" pos="{BLUE}">
      <joint type="free"/>
      <geom type="box" size="0.025 0.025 0.025"
            rgba="0.2 0.2 0.9 1" mass="0.1"
            contype="1" conaffinity="1"/>
      <inertial pos="0 0 0" mass="0.1"
                diaginertia="0.0005 0.0005 0.0005"/>
    </body>
    <body name="green_cylinder" pos="{GREEN}">
      <joint type="free"/>
      <geom type="cylinder" size="0.03 0.05"
            rgba="0.2 0.8 0.2 1" mass="0.2"
            contype="1" conaffinity="1"/>
      <inertial pos="0 0 0" mass="0.2"
                diaginertia="0.001 0.001 0.001"/>
    </body>
    <body name="container" pos="{TARGET}">
      <geom type="box" size="0.10 0.10 0.01"
            rgba="0.3 0.3 0.3 1" mass="5"
            contype="1" conaffinity="1"/>
      <inertial pos="0 0 0" mass="5"
                diaginertia="1 1 1"/>
    </body>
"""

with open("body.py", "r") as f:
    content = f.read()

# Replace entire objects block with clean version
new_content = re.sub(
    r'objects\s*=\s*""".*?"""',
    f'objects = """{NEW_OBJECTS}"""',
    content,
    flags=re.DOTALL
)

# Also fix the broken scene.replace call
new_content = re.sub(
    r"scene\.replace\(\s*['\"].*?['\"],",
    "scene = scene.replace('</worldbody>',",
    new_content,
    flags=re.DOTALL
)

with open("body.py", "w") as f:
    f.write(new_content)

print("\nbody.py fixed!")

# Fix POINT_B in main.py
with open("main.py", "r") as f:
    main = f.read()
main = re.sub(
    r'POINT_B\s*=\s*\[.*?\]',
    f'POINT_B = [{TABLE_X-0.10:.3f}, {TABLE_Y-0.15:.3f}, {TABLE_SURFACE:.3f}]',
    main)
with open("main.py", "w") as f:
    f.write(main)
print("main.py POINT_B fixed!")
