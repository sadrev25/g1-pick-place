import os
import numpy as np
from vision.detector import VisionPipeline
from stable_baselines3 import PPO
from brain         import process_command, validate_joints
from body          import RobotBody
from ik_controller import IKController

POINT_B = [0.230, -0.149, 0.878]

OBJECT_MAP = {
    'red':          'red_cube',
    'red_cube':     'red_cube',
    'blue':         'blue_cube',
    'blue_cube':    'blue_cube',
    'small':        'blue_cube',
    'green':        'green_cylinder',
    'cylinder':     'green_cylinder',
    'all':          'all',
}

def parse_object(command):
    cmd = command.lower()
    for key, val in OBJECT_MAP.items():
        if key in cmd:
            return val
    return None

def run():
    print("\n" + "="*45)
    print("  G1 Pick and Place System")
    print("  Brain: GPT-4o  |  IK: Jacobian")
    print("  Hand: Auto-selected by position")
    print("="*45)

    robot = RobotBody()
    robot.start()

    ik = IKController(
        robot.model, robot.data, robot.viewer)
    vision = VisionPipeline(
        robot.model, robot.data)

    # Load residual RL policy
    try:
        residual_policy = PPO.load(
            "models/best/best_model")
        print("✅ Residual RL loaded!")
    except Exception as e:
        residual_policy = None
        print(f"⚠️  No residual: {e}")

    print("\nCommands:")
    print("  'pick the red cube'    → right hand")
    print("  'pick the blue cube'   → left hand")
    print("  'pick the green one'   → right hand")
    print("  'pick all objects'     → auto hand")
    print("  'raise your right arm' → GPT-4 move")
    print("  'go home'              → reset")
    print("  'quit'                 → exit")
    print("="*45 + "\n")

    history = []

    while robot.is_running():
        try:
            cmd = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not cmd:
            continue

        if cmd.lower() in ['quit','q','exit']:
            break

        is_pick = any(w in cmd.lower()
                      for w in ['pick','grab',
                                 'take','get'])

        if is_pick:
            obj = parse_object(cmd)
            if obj == 'all':
                for name in ['red_cube',
                              'green_cylinder',
                              'blue_cube']:
                    ik.pick_sequence(
                        name,
                        place_pos=POINT_B)
            elif obj:
                # Vision: detect position
                _, pos = vision.get_object_position(cmd)
                if pos is not None:
                    import mujoco as mj
                    bid = mj.mj_name2id(
                        robot.model,
                        mj.mjtObj.mjOBJ_BODY,
                        obj)
                    for j in range(
                            robot.model.njnt):
                        if robot.model.jnt_bodyid[j] == bid:
                            adr = robot.model.jnt_qposadr[j]
                            robot.data.qpos[adr:adr+3] = pos
                            mj.mj_forward(
                                robot.model,
                                robot.data)
                            print(f"Updated {obj} to {pos}")
                            break
                # Apply residual
                if False:  # disabled - v2 coming
                    import numpy as _np
                    import mujoco as _mj
                    bid = _mj.mj_name2id(
                        robot.model,
                        _mj.mjtObj.mjOBJ_BODY,
                        obj)
                    _mj.mj_forward(
                        robot.model,
                        robot.data)
                    hand = robot.data.xpos[
                        ik.r_wrist].copy()
                    obj_p = robot.data.xpos[
                        bid].copy()
                    tgt  = _np.array(POINT_B)
                    # Obs must match training exactly
                    # hand(3)+obj(3)+target(3)+phase(1)=10
                    phase = _np.array([0.0])
                    obs  = _np.concatenate([
                        hand,
                        obj_p,
                        tgt,
                        phase
                    ]).astype(_np.float32)
                    print(f"Obs: {obs.round(3)}")
                    action, _ = (
                        residual_policy
                        .predict(obs,
                        deterministic=True))
                    # v1: action=[dx,dy,dz]
                    # Apply as offset to object pos
                    # so IK targets corrected position
                    corrected = obj_p + action
                    for j in range(
                            robot.model.njnt):
                        if robot.model.jnt_bodyid[j] == bid:
                            adr = robot.model.jnt_qposadr[j]
                            robot.data.qpos[adr:adr+3] = corrected
                            _mj.mj_forward(
                                robot.model,
                                robot.data)
                            break
                    print(f"Residual: {action.round(3)}")
                    print(f"Corrected pos: {corrected.round(3)}")
                ik.pick_sequence(
                    obj,
                    place_pos=POINT_B)
            else:
                print("Robot: Which object? "
                      "red, blue or green?\n")
            continue

        if cmd.lower() in ['home','reset']:
            ik._go_home()
            print("Robot: Home!\n")
            continue

        result = process_command(cmd, history)
        if result is None:
            print("Robot: Did not understand.\n")
            continue

        result['joints'] = validate_joints(
            result.get('joints', {}))
        robot.execute(result)
        history.append({
            "command":  cmd,
            "response": result
        })
        print(f"Robot: {result['message']}\n")

if __name__ == "__main__":
    run()
