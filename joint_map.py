# NEW joint map after removing legs
# Legs removed — only waist + arms remain

JOINT_MAP = {
    # Waist
    "waist_yaw":            {"ctrl": 0,  "range": [-1.5,  1.5]},
    "waist_roll":           {"ctrl": 1,  "range": [-0.5,  0.5]},
    "waist_pitch":          {"ctrl": 2,  "range": [-0.5,  0.8]},
    # Left arm
    "left_shoulder_pitch":  {"ctrl": 3,  "range": [-1.5,  3.0]},
    "left_shoulder_roll":   {"ctrl": 4,  "range": [-0.5,  2.5]},
    "left_shoulder_yaw":    {"ctrl": 5,  "range": [-1.5,  1.5]},
    "left_elbow":           {"ctrl": 6,  "range": [-2.5,  0.0]},
    "left_wrist_roll":      {"ctrl": 7,  "range": [-1.5,  1.5]},
    "left_wrist_pitch":     {"ctrl": 8,  "range": [-1.0,  1.0]},
    "left_wrist_yaw":       {"ctrl": 9,  "range": [-1.5,  1.5]},
    # Right arm
    "right_shoulder_pitch": {"ctrl": 10, "range": [-1.5,  3.0]},
    "right_shoulder_roll":  {"ctrl": 11, "range": [-2.5,  0.5]},
    "right_shoulder_yaw":   {"ctrl": 12, "range": [-1.5,  1.5]},
    "right_elbow":          {"ctrl": 13, "range": [-2.5,  0.0]},
    "right_wrist_roll":     {"ctrl": 14, "range": [-1.5,  1.5]},
    "right_wrist_pitch":    {"ctrl": 15, "range": [-1.0,  1.0]},
    "right_wrist_yaw":      {"ctrl": 16, "range": [-1.5,  1.5]},
}

def get_joint_map_string():
    lines = ["Available joints (name: ctrl_index, range):"]
    for name, info in JOINT_MAP.items():
        lines.append(
            f"  {name}: ctrl[{info['ctrl']}], "
            f"range[{info['range'][0]}, "
            f"{info['range'][1]}]")
    return "\n".join(lines)
