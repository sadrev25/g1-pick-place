import openai
import base64
import json
import os

class GPT4oDetector:
    def __init__(self):
        self.client = openai.OpenAI(
            api_key=os.environ["OPENAI_API_KEY"])
        print("GPT-4o ready!")

    def _encode(self, path):
        with open(path, "rb") as f:
            return base64.b64encode(
                f.read()).decode("utf-8")

    def identify(self, image_path, command):
        """
        GPT-4o identifies WHICH object
        the user wants to pick.
        Returns color string for OpenCV.
        """
        b64 = self._encode(image_path)

        prompt = f"""
User command: "{command}"

Look at this robot simulation image.
There are colored objects on a table:
red cube, blue cube, green cylinder.

Which object does the user want to pick?
Return ONLY this JSON:
{{"color": "red", "object": "red_cube"}}

Color must be one of: red, blue, green
Object must be one of: red_cube, blue_cube,
green_cylinder
"""
        try:
            resp = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{b64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }],
                max_tokens=50)

            raw = resp.choices[0].message.content
            raw = raw.strip()
            if "```" in raw:
                raw = raw.split(
                    "```")[1].strip()
                if raw.startswith("json"):
                    raw = raw[4:].strip()

            result = json.loads(raw)
            color  = result["color"]
            obj    = result["object"]
            print(f"GPT-4o identified: "
                  f"{obj} (color={color})")
            return color, obj

        except Exception as e:
            print(f"GPT-4o error: {e}")
            return None, None
