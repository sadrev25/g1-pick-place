import ast

with open('main.py', 'r') as f:
    content = f.read()

# Step 1: Add PPO import
if 'from stable_baselines3' not in content:
    content = content.replace(
        'from vision.detector import VisionPipeline',
        'from vision.detector import VisionPipeline\n'
        'from stable_baselines3 import PPO\n'
        'import numpy as np as np2')
    # simpler
    content = content.replace(
        'from stable_baselines3 import PPO\n'
        'import numpy as np as np2',
        'from stable_baselines3 import PPO')
    print("Import added!")

# Step 2: Load residual after vision init
OLD = ('    vision = VisionPipeline(\n'
       '        robot.model, robot.data)')
NEW = ('    vision = VisionPipeline(\n'
       '        robot.model, robot.data)\n'
       '\n'
       '    # Load residual RL policy\n'
       '    try:\n'
       '        residual_policy = PPO.load(\n'
       '            "models/best/best_model")\n'
       '        print("✅ Residual RL loaded!")\n'
       '    except Exception as e:\n'
       '        residual_policy = None\n'
       '        print(f"⚠️  No residual: {e}")')

if OLD in content:
    content = content.replace(OLD, NEW)
    print("Residual init added!")
else:
    print("Vision pattern not found!")
    for i, line in enumerate(
            content.split('\n')):
        if 'VisionPipeline' in line:
            print(f"  {i+1}: {line}")

# Step 3: Apply residual before pick
OLD_PICK = ('                ik.pick_sequence(\n'
            '                    obj,\n'
            '                    place_pos=POINT_B)')

NEW_PICK = ('                # Apply residual\n'
            '                if residual_policy:\n'
            '                    import numpy as _np\n'
            '                    import mujoco as _mj\n'
            '                    bid = _mj.mj_name2id(\n'
            '                        robot.model,\n'
            '                        _mj.mjtObj.mjOBJ_BODY,\n'
            '                        obj)\n'
            '                    _mj.mj_forward(\n'
            '                        robot.model,\n'
            '                        robot.data)\n'
            '                    hand = robot.data.xpos[\n'
            '                        ik.r_wrist].copy()\n'
            '                    obj_p = robot.data.xpos[\n'
            '                        bid].copy()\n'
            '                    tgt  = _np.array(POINT_B)\n'
            '                    obs  = _np.concatenate([\n'
            '                        hand, obj_p,\n'
            '                        tgt, [0.0]\n'
            '                    ]).astype(_np.float32)\n'
            '                    action, _ = (\n'
            '                        residual_policy\n'
            '                        .predict(obs,\n'
            '                        deterministic=True))\n'
            '                    # Apply correction\n'
            '                    for i, idx in enumerate(\n'
            '                            ik.r_arm_ctrls):\n'
            '                        if i < len(action):\n'
            '                            robot.data.ctrl[\n'
            '                                idx] += action[i]\n'
            '                    _mj.mj_forward(\n'
            '                        robot.model,\n'
            '                        robot.data)\n'
            '                    print(f"Residual: {action.round(3)}")\n'
            '                ik.pick_sequence(\n'
            '                    obj,\n'
            '                    place_pos=POINT_B)')

if OLD_PICK in content:
    content = content.replace(
        OLD_PICK, NEW_PICK)
    print("Residual pick added!")
else:
    print("pick_sequence pattern not found!")
    for i, line in enumerate(
            content.split('\n')):
        if 'pick_sequence' in line:
            print(f"  {i+1}: {line}")

with open('main.py', 'w') as f:
    f.write(content)

try:
    ast.parse(content)
    print("✅ main.py OK!")
except SyntaxError as e:
    print(f"❌ line {e.lineno}: {e.msg}")
