import re
with open('ik_controller.py', 'r') as f:
    content = f.read()

# Find grasp_object and print it
lines = content.split('\n')
for i, line in enumerate(lines):
    if 'def grasp_object' in line:
        print('\n'.join(lines[i:i+20]))
        break
