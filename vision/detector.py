import numpy as np
from vision.camera import MuJoCoCamera
from vision.gpt4o  import GPT4oDetector

class VisionPipeline:
    """
    Full pipeline:
    1. GPT-4o identifies which object
    2. OpenCV finds exact pixel position
    3. Camera matrix converts to world xyz
    4. Returns xyz for IK
    """

    def __init__(self, model, data):
        self.cam = MuJoCoCamera(model, data)
        self.gpt = GPT4oDetector()
        print("Vision pipeline ready!")

    def get_object_position(self, command,
                             known_z=0.878):
        """
        Main function — call this before pick.
        Returns (obj_name, world_xyz) or
                (None, None) if failed.
        """
        # Step 1: capture scene
        print("\n[Vision] Capturing scene...")
        img_path, pixels = self.cam.capture()

        # Step 2: GPT-4o identifies object
        print("[Vision] Asking GPT-4o...")
        color, obj_name = self.gpt.identify(
            img_path, command)

        if color is None:
            print("[Vision] GPT-4o failed!")
            return None, None

        # Step 3: OpenCV finds pixel center
        print(f"[Vision] Finding {color} "
              f"object in image...")
        pixel = self.cam.detect_color(
            pixels, color)

        if pixel is None:
            print(f"[Vision] Color '{color}' "
                  f"not found in image!")
            return obj_name, None

        # Step 4: pixel → world xyz
        print("[Vision] Converting to 3D...")
        cx, cy = pixel
        world_pos = self.cam.pixel_to_world(
            cx, cy, known_z=known_z)

        if world_pos is None:
            print("[Vision] 3D conversion failed!")
            return obj_name, None

        print(f"[Vision] Done! "
              f"{obj_name} at {world_pos}")
        return obj_name, world_pos
