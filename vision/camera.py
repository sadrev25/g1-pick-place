import mujoco
import numpy as np
import cv2

class MuJoCoCamera:
    def __init__(self, model, data,
                 width=640, height=480):
        self.model  = model
        self.data   = data
        self.w      = width
        self.h      = height

        self.renderer      = mujoco.Renderer(
            model, height=height, width=width)
        self.cam           = mujoco.MjvCamera()
        self.cam.type      = mujoco.mjtCamera.mjCAMERA_FREE
        self.cam.lookat[0] = 0.23
        self.cam.lookat[1] = -0.149
        self.cam.lookat[2] = 0.878
        self.cam.distance  = 1.5
        self.cam.azimuth   = 180
        self.cam.elevation = -25
        print("Camera ready!")

    def capture(self, save_path="/tmp/frame.jpg"):
        mujoco.mj_forward(self.model, self.data)
        self.renderer.update_scene(
            self.data, self.cam)
        pixels = self.renderer.render()
        img = cv2.cvtColor(
            pixels, cv2.COLOR_RGB2BGR)
        cv2.imwrite(save_path, img)
        return save_path, pixels

    def detect_color(self, pixels, color="red"):
        """
        OpenCV color detection.
        Returns (cx, cy) pixel center of object.
        """
        hsv = cv2.cvtColor(
            pixels, cv2.COLOR_RGB2HSV)

        masks = {
            "red": (
                np.array([0,   120, 70]),
                np.array([10,  255, 255])),
            "blue": (
                np.array([100, 150, 0]),
                np.array([140, 255, 255])),
            "green": (
                np.array([40,  40,  40]),
                np.array([80,  255, 255])),
        }

        if color not in masks:
            return None

        lo, hi = masks[color]
        mask   = cv2.inRange(hsv, lo, hi)

        # Clean up noise
        kernel = np.ones((5,5), np.uint8)
        mask   = cv2.morphologyEx(
            mask, cv2.MORPH_OPEN, kernel)
        mask   = cv2.morphologyEx(
            mask, cv2.MORPH_CLOSE, kernel)

        M = cv2.moments(mask)
        if M["m00"] < 100:  # too small
            return None

        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        print(f"Color '{color}' at pixel "
              f"({cx}, {cy})")
        return cx, cy

    def pixel_to_world(self, cx, cy,
                       known_z=0.878):
        """
        Convert pixel (cx,cy) to world xyz.
        Uses known table height z=0.878.

        Method: unproject pixel through
        camera matrix using MuJoCo's own
        camera parameters.
        """
        # Get camera matrices from MuJoCo
        scene = mujoco.MjvScene(
            self.model, maxgeom=1000)
        self.renderer.update_scene(
            self.data, self.cam)

        # Get projection and view matrices
        # from renderer scene
        fovy   = np.radians(self.cam.fovy
                             if hasattr(
                                 self.cam,'fovy')
                             else 45)
        aspect = self.w / self.h
        fovx   = 2 * np.arctan(
            np.tan(fovy/2) * aspect)

        # Normalized device coordinates
        # cx,cy in [0,W] x [0,H]
        # → NDC in [-1,1] x [-1,1]
        ndc_x = (cx / self.w) * 2 - 1
        ndc_y = 1 - (cy / self.h) * 2

        # Camera position
        # From azimuth/elevation/distance
        az  = np.radians(self.cam.azimuth)
        el  = np.radians(self.cam.elevation)
        d   = self.cam.distance

        cam_x = (self.cam.lookat[0]
                 + d * np.cos(el) * np.sin(az))
        cam_y = (self.cam.lookat[1]
                 - d * np.cos(el) * np.cos(az))
        cam_z = (self.cam.lookat[2]
                 + d * np.sin(el))

        cam_pos = np.array([cam_x, cam_y, cam_z])
        lookat  = np.array([
            self.cam.lookat[0],
            self.cam.lookat[1],
            self.cam.lookat[2]])

        # Camera axes
        forward = lookat - cam_pos
        forward = forward / np.linalg.norm(forward)
        world_up = np.array([0, 0, 1.0])
        right    = np.cross(forward, world_up)
        right    = right / np.linalg.norm(right)
        up       = np.cross(right, forward)

        # Ray direction
        ray = (forward
               + ndc_x * np.tan(fovx/2) * right
               + ndc_y * np.tan(fovy/2) * up)
        ray = ray / np.linalg.norm(ray)

        # Intersect ray with plane z=known_z
        if abs(ray[2]) < 1e-6:
            return None

        t = (known_z - cam_pos[2]) / ray[2]
        if t < 0:
            return None

        world = cam_pos + t * ray
        print(f"Pixel ({cx},{cy}) → "
              f"world [{world[0]:.3f}, "
              f"{world[1]:.3f}, "
              f"{world[2]:.3f}]")
        return world
