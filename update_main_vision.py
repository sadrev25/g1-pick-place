import ast

with open('main.py', 'r') as f:
    content = f.read()

# Add import
if 'VisionPipeline' not in content:
    content = content.replace(
        'from brain',
        'from vision.detector '
        'import VisionPipeline\n'
        'from brain')
    print("Import added!")

# Init after IK
OLD = ('    ik = IKController(\n'
       '        robot.model, robot.data,'
       ' robot.viewer)')
NEW = ('    ik = IKController(\n'
       '        robot.model, robot.data,'
       ' robot.viewer)\n'
       '    vision = VisionPipeline(\n'
       '        robot.model, robot.data)')

if OLD in content:
    content = content.replace(OLD, NEW)
    print("Vision init added!")

# Replace pick call
OLD_PICK = ('                ik.pick_sequence(\n'
            '                    obj_name,\n'
            '                    place_pos=POINT_B)')

NEW_PICK = ('                # Vision detects\n'
            '                _, pos = vision\\\n'
            '                    .get_object_position(\n'
            '                    command)\n'
            '                if pos is not None:\n'
            '                    import mujoco as mj\n'
            '                    bid = mj.mj_name2id(\n'
            '                        robot.model,\n'
            '                        mj.mjtObj.mjOBJ_BODY,\n'
            '                        obj_name)\n'
            '                    for j in range(\n'
            '                        robot.model.njnt):\n'
            '                      if (robot.model\n'
            '                          .jnt_bodyid[j]\n'
            '                          == bid):\n'
            '                        adr = (robot.model\n'
            '                               .jnt_qposadr[j])\n'
            '                        robot.data\\\n'
            '                            .qpos[adr:adr+3]\\\n'
            '                            = pos\n'
            '                        mj.mj_forward(\n'
            '                          robot.model,\n'
            '                          robot.data)\n'
            '                        break\n'
            '                ik.pick_sequence(\n'
            '                    obj_name,\n'
            '                    place_pos=POINT_B)')

if OLD_PICK in content:
    content = content.replace(OLD_PICK, NEW_PICK)
    print("Pick sequence updated!")
else:
    print("pick_sequence not found — check manually")
    for i, l in enumerate(content.split('\n')):
        if 'pick_sequence' in l:
            print(f"  {i+1}: {l}")

with open('main.py', 'w') as f:
    f.write(content)

try:
    ast.parse(content)
    print("main.py OK!")
except SyntaxError as e:
    print(f"Error {e.lineno}: {e.msg}")
