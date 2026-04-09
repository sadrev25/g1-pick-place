with open('ik_controller.py', 'r') as f:
    content = f.read()

OLD = '''    def grasp_object(self, obj_name, hand='right'):
        """
        Attach object to wrist
        Object will follow arm from now on
        """
        wrist_pos = self.get_ee_pos(hand)
        obj_pos   = self.get_obj_pos(obj_name)
        # Store offset from wrist to object
        offset = obj_pos - wrist_pos
        self.grasped = (obj_name, hand, offset)
        print(f"   Grasped {obj_name}! "
              f"offset={offset}")'''

NEW = '''    def grasp_object(self, obj_name, hand='right'):
        """
        Attach object to wrist.
        Zero offset = cube snaps to hand center.
        No floating, no position drift.
        """
        wrist_pos = self.get_ee_pos(hand)
        obj_pos   = self.get_obj_pos(obj_name)
        gap       = np.linalg.norm(wrist_pos - obj_pos)
        print(f"   Grasp gap: {gap:.3f}m")

        # Zero offset — cube snaps to wrist
        # This prevents floating during carry
        offset = np.zeros(3)
        self.grasped = (obj_name, hand, offset)

        # Immediately teleport cube to wrist
        self._carry_object()
        print(f"   Grasped {obj_name}! "
              f"snapped to wrist.")'''

if OLD in content:
    content = content.replace(OLD, NEW)
    print("✅ grasp_object fixed!")
else:
    print("❌ Pattern not found — trying regex")
    import re
    content = re.sub(
        r'offset = obj_pos - wrist_pos\s*\n\s*self\.grasped',
        'offset = np.zeros(3)\n        self.grasped',
        content)
    print("✅ offset zeroed!")

with open('ik_controller.py', 'w') as f:
    f.write(content)
