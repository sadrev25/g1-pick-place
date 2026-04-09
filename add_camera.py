import ast

with open('body.py', 'r') as f:
    content = f.read()

# The pattern from grep output is exact
OLD = '        objects + "</worldbody>")'

NEW = ('        objects'
       ' + \'<camera name="frontcam"'
       ' pos="0.0 -1.0 1.3"'
       ' xyaxes="1 0 0 0 0.6 1"'
       ' fovy="55"/>\''
       ' + "</worldbody>")')

if OLD in content:
    content = content.replace(OLD, NEW)
    print("Camera added!")
else:
    print("Not found, trying...")
    print(repr(content[content.find('worldbody')-5:
                        content.find('worldbody')+50]))

with open('body.py', 'w') as f:
    f.write(content)

try:
    ast.parse(content)
    print("Syntax OK!")
except SyntaxError as e:
    print(f"Error {e.lineno}: {e.msg}")
