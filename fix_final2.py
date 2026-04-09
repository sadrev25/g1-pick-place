with open('body.py', 'r') as f:
    lines = f.readlines()

# Print lines 118-130 to see full damage
for i, line in enumerate(lines[117:130], start=118):
    print(f"{i}: {repr(line)}")

# Remove ALL broken lines after worldbody cameras
clean = []
for line in lines:
    stripped = line.strip()
    # Skip all these broken patterns
    if stripped == '"':
        continue
    if stripped == '",':
        continue
    if stripped == "objects + '":
        continue
    if stripped == "objects + \"":
        continue
    if '</worldbody>",' in line:
        continue
    if 'objects + ' in line and '<' not in line:
        continue
    clean.append(line)

with open('body.py', 'w') as f:
    f.writelines(clean)

import ast
with open('body.py') as f:
    content = f.read()
try:
    ast.parse(content)
    print("body.py OK!")
except SyntaxError as e:
    print(f"Error line {e.lineno}: {e.msg}")
    lines2 = content.split('\n')
    for j in range(max(0,e.lineno-3),
                   min(len(lines2),e.lineno+3)):
        print(f"  {j+1}: {repr(lines2[j])}")
