with open('main.py', 'r') as f:
    content = f.read()

OLD = ('            elif obj:\n'
       '                ik.pick_sequence(\n'
       '                    obj,\n'
       '                    place_pos=POINT_B)')

NEW = ('            elif obj:\n'
       '                # Vision: detect position\n'
       '                _, pos = vision.get_object_position(cmd)\n'
       '                if pos is not None:\n'
       '                    import mujoco as mj\n'
       '                    bid = mj.mj_name2id(\n'
       '                        robot.model,\n'
       '                        mj.mjtObj.mjOBJ_BODY,\n'
       '                        obj)\n'
       '                    for j in range(\n'
       '                            robot.model.njnt):\n'
       '                        if robot.model.jnt_bodyid[j] == bid:\n'
       '                            adr = robot.model.jnt_qposadr[j]\n'
       '                            robot.data.qpos[adr:adr+3] = pos\n'
       '                            mj.mj_forward(\n'
       '                                robot.model,\n'
       '                                robot.data)\n'
       '                            print(f"Updated {obj} to {pos}")\n'
       '                            break\n'
       '                ik.pick_sequence(\n'
       '                    obj,\n'
       '                    place_pos=POINT_B)')

if OLD in content:
    content = content.replace(OLD, NEW)
    print("Vision wired into pick!")
else:
    print("Pattern not found!")

with open('main.py', 'w') as f:
    f.write(content)

import ast
try:
    ast.parse(content)
    print("main.py OK!")
except SyntaxError as e:
    print(f"Error {e.lineno}: {e.msg}")
