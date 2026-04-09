import shutil, ast

# Restore from clean backup
shutil.copy('assets/body_backup.py', 'body.py')
print("Restored from backup!")

# Read it
with open('body.py', 'r') as f:
    content = f.read()

# Find the objects = """ block and add camera inside it
# Camera XML goes OUTSIDE worldbody in MuJoCo
# So we add it to the scene after worldbody closes
# Safest: add camera to objects string directly

OLD = '    scene = scene.replace(\n        \'</worldbody>\','
NEW = (
    '    cameras = (\n'
    '        \'<camera name="frontcam"\'\n'
    '        \' pos="0.0 -1.0 1.3"\'\n'
    '        \' xyaxes="1 0 0 0 0.6 1"\'\n'
    '        \' fovy="55"/>\'\n'
    '    )\n'
    '    scene = scene.replace(\n'
    '        \'</worldbody>\',\n'
    '        cameras +\n'
    '        \'</worldbody>\',\n'
    '    )\n'
    '    scene = scene.replace(\n'
    '        \'</worldbody>\','
)

if OLD in content:
    content = content.replace(OLD, NEW)
    print("Camera added!")
else:
    print("Pattern not found!")
    print("Looking for replace calls...")
    for i,line in enumerate(content.split('\n')):
        if 'replace' in line or 'worldbody' in line:
            print(f"  {i+1}: {line}")

with open('body.py', 'w') as f:
    f.write(content)

try:
    ast.parse(content)
    print("body.py syntax OK!")
except SyntaxError as e:
    print(f"Error line {e.lineno}: {e.msg}")
    lines = content.split('\n')
    for j in range(max(0,e.lineno-3),
                   min(len(lines),e.lineno+3)):
        print(f"  {j+1}: {repr(lines[j])}")
