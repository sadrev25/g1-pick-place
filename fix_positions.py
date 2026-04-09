import re

with open('body.py', 'r') as f:
    content = f.read()

# From reset_scene.py output:
# Wrist natural reach: [0.233, -0.172, 1.008]
# These are MEASURED positions!

new_objects = """
    <body name="table"
          pos="0.23 -0.17 0.96">
      <geom type="box" size="0.15 0.12 0.01"
            rgba="0.6 0.4 0.2 1" mass="20"
            contype="1" conaffinity="1"/>
      <inertial pos="0 0 0" mass="20"
                diaginertia="1 1 1"/>
    </body>
    <body name="red_cube"
          pos="0.23 -0.17 1.01">
      <joint type="free"/>
      <geom type="box" size="0.04 0.04 0.04"
            rgba="0.9 0.2 0.2 1" mass="0.3"
            contype="1" conaffinity="1"/>
      <inertial pos="0 0 0" mass="0.3"
                diaginertia="0.001 0.001 0.001"/>
    </body>
    <body name="blue_cube"
          pos="0.23 -0.11 0.99">
      <joint type="free"/>
      <geom type="box" size="0.025 0.025 0.025"
            rgba="0.2 0.2 0.9 1" mass="0.1"
            contype="1" conaffinity="1"/>
      <inertial pos="0 0 0" mass="0.1"
          diaginertia="0.0005 0.0005 0.0005"/>
    </body>
    <body name="green_cylinder"
          pos="0.23 -0.23 1.02">
      <joint type="free"/>
      <geom type="cylinder" size="0.03 0.05"
            rgba="0.2 0.8 0.2 1" mass="0.2"
            contype="1" conaffinity="1"/>
      <inertial pos="0 0 0" mass="0.2"
                diaginertia="0.001 0.001 0.001"/>
    </body>
    <body name="container"
          pos="0.13 -0.32 0.96">
      <geom type="box" size="0.10 0.10 0.01"
            rgba="0.3 0.3 0.3 1" mass="5"
            contype="1" conaffinity="1"/>
      <inertial pos="0 0 0" mass="5"
                diaginertia="1 1 1"/>
    </body>
"""

# Find and replace objects section
pattern = re.compile(
    r'<body name="table".*?</body>\s*'
    r'<body name="red_cube".*?</body>\s*'
    r'<body name="blue_cube".*?</body>\s*'
    r'<body name="green_cylinder".*?</body>\s*'
    r'<body name="container".*?</body>',
    re.DOTALL)

if pattern.search(content):
    content = pattern.sub(
        new_objects.strip(), content)
    print("✅ Objects replaced!")
else:
    print("Pattern not found!")
    print("Adding before </worldbody>...")
    # Remove old objects first
    for name in ['table','red_cube','blue_cube',
                 'green_cylinder','container']:
        old = re.compile(
            r'\s*<body name="'+name+r'".*?</body>',
            re.DOTALL)
        content = old.sub('', content)
    # Add new ones
    content = content.replace(
        '</worldbody>',
        new_objects + '\n    </worldbody>')
    print("✅ Objects added!")

with open('body.py', 'w') as f:
    f.write(content)

# Update Point B
with open('main.py', 'r') as f:
    main = f.read()
main = re.sub(
    r'POINT_B = \[.*?\]',
    'POINT_B = [0.13, -0.32, 0.97]',
    main)
with open('main.py', 'w') as f:
    f.write(main)

print("✅ Point B updated!")
print("\nPositions set to MEASURED values:")
print("  table:      0.23 -0.17 0.96")
print("  red_cube:   0.23 -0.17 1.01")
print("  blue_cube:  0.23 -0.11 0.99")
print("  green_cyl:  0.23 -0.23 1.02")
print("  container:  0.13 -0.32 0.96")
print("  point_B:    0.13 -0.32 0.97")
