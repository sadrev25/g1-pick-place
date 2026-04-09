with open('body.py', 'r') as f:
    lines = f.readlines()

clean = []
skip_next = 0
for i, line in enumerate(lines):
    stripped = line.strip()
    # Skip all broken junk lines
    bad = [
        '</worldbody>",',
        '</worldbody>")',
        'objects + "',
        "objects + '",
    ]
    if any(b in stripped for b in bad):
        print(f"Skip line {i+1}: {repr(line.rstrip())}")
        continue
    # Fix duplicate camera blocks - keep only first
    if 'frontcam' in line and i > 120:
        print(f"Skip dup camera line {i+1}")
        continue
    if 'topcam' in line and i > 121:
        print(f"Skip dup camera line {i+1}")
        continue
    clean.append(line)

# Now fix the scene.replace call
# Find where objects string ends and fix closing
result = []
for i, line in enumerate(clean):
    result.append(line)

with open('body.py', 'w') as f:
    f.writelines(result)

# Final check - fix scene.replace
with open('body.py', 'r') as f:
    content = f.read()

import re
# Remove broken closing and add correct one
content = re.sub(
    r'"""[\s\n]*</worldbody>["\),\s]+',
    '"""\n    scene = scene.replace(\n        "</worldbody>",\n        objects + "</worldbody>")\n',
    content)

with open('body.py', 'w') as f:
    f.write(content)

import ast
try:
    ast.parse(content)
    print("body.py OK!")
except SyntaxError as e:
    print(f"Error line {e.lineno}: {e.msg}")
    lines2 = content.split('\n')
    for j in range(max(0,e.lineno-3),
                   min(len(lines2),e.lineno+3)):
        print(f"  {j+1}: {repr(lines2[j])}")
