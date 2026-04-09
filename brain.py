import openai
import json
import os
from joint_map import get_joint_map_string, JOINT_MAP

client = openai.OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = f"""
You are the brain of a Unitree G1 humanoid robot.
Translate human commands into joint angle values.

{get_joint_map_string()}

Rules:
1. Return ONLY valid JSON, nothing else
2. Only include joints that need to change
3. Keep values within joint ranges
4. For home/reset return empty joints dict

Return this exact format:
{{
    "action": "what robot will do",
    "joints": {{
        "joint_name": value
    }},
    "message": "friendly response"
}}

Examples:

Command: "raise your right arm"
{{
    "action": "raising right arm",
    "joints": {{
        "right_shoulder_pitch": 1.2,
        "right_shoulder_roll": -0.3,
        "right_elbow": -0.5
    }},
    "message": "Raising my right arm!"
}}

Command: "reach toward the table"
{{
    "action": "reaching toward table",
    "joints": {{
        "waist_pitch": 0.3,
        "right_shoulder_pitch": 1.2,
        "right_shoulder_roll": -0.2,
        "right_elbow": -0.8,
        "right_wrist_pitch": 0.3
    }},
    "message": "Reaching toward the table!"
}}

Command: "go home"
{{
    "action": "returning to neutral",
    "joints": {{}},
    "message": "Going home!"
}}
"""

def process_command(command, history=None):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if history:
        for h in history[-3:]:
            messages.append({"role": "user",
                              "content": h["command"]})
            messages.append({"role": "assistant",
                              "content": json.dumps(h["response"])})

    messages.append({"role": "user", "content": command})

    print(f"   Brain: thinking...")
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=400,
            temperature=0.3,
        )
        raw = response.choices[0].message.content
        raw = raw.replace("```json","").replace("```","").strip()
        result = json.loads(raw)
        print(f"   Brain: {result['message']}")
        return result
    except Exception as e:
        print(f"   Brain: error {e}")
        return None

def validate_joints(joints):
    safe = {}
    for name, value in joints.items():
        if name in JOINT_MAP:
            lo = JOINT_MAP[name]["range"][0]
            hi = JOINT_MAP[name]["range"][1]
            safe[name] = max(lo, min(hi, value))
    return safe
