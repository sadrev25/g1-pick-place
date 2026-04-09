with open('body.py', 'r') as f:
    lines = f.readlines()

print(f"Line 115: {repr(lines[114])}")

# Keep only clean lines
clean = []
for line in lines:
    stripped = line.strip()
    # Skip broken lines
    if stripped == '"':
        print(f"Skipping lone quote")
        continue
    if 'grasp_object: command' in line:
        continue
    if '<- Cube teleports' in line:
        continue
    clean.append(line)

with open('body.py', 'w') as f:
    f.writelines(clean)

# Add cameras using string concatenation
with open('body.py', 'r') as f:
    content = f.read()

import re
content = re.sub(r'<camera[^>]*/>', '', content)

cam_xml = '    <camera name="frontcam" pos="0.3 -0.8 1.2" xyaxes="1 0 0 0 0.5 1" fovy="60"/>\n'
cam_xml += '    <camera name="topcam" pos="0.23 -0.15 1.8" xyaxes="1 0 0 0 1 0" fovy="60"/>\n'

if 'frontcam' not in content:
    content = content.replace('</worldbody>', cam_xml + '</worldbody>')

with open('body.py', 'w') as f:
    f.write(content)

import ast
try:
    ast.parse(content)
    print("body.py OK!")
except SyntaxError as e:
    print(f"Error line {e.lineno}: {e.msg}")
    lines2 = content.split('\n')
    for j in range(max(0,e.lineno-3), min(len(lines2),e.lineno+3)):
        print(f"  {j+1}: {repr(lines2[j])}")
