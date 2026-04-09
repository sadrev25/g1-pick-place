with open('ik_controller.py', 'r') as f:
    content = f.read()

OLD = '''        # Step 1 — above object
        print("\\n[1] Moving above object...")
        above     = obj_pos.copy()
        above[2] += 0.10
        ok = self.move_to(above, hand)
        if not ok:
            print("❌ Cannot reach!")
            self._go_home()
            return False
        self._hold(150)
        # Step 2 — align XY with object
        print("\\n[2] Aligning...")
        align    = obj_pos.copy()
        align[2] = self.get_ee_pos(hand)[2]
        self.move_to(align, hand, tolerance=0.02)
        self._hold(150)
        # Step 3 — move down to object
        print("\\n[3] Moving to object...")
        self.move_to(obj_pos, hand,
                      tolerance=0.04)
        self._hold(200)
        # Step 4 — GRASP (attach object)
        print("\\n[4] Grasping...")
        self.grasp_object(obj_name, hand)
        self._hold(200)'''

NEW = '''        # Step 1 — move above object
        print("\\n[1] Moving above object...")
        above     = obj_pos.copy()
        above[2] += 0.10
        ok = self.move_to(above, hand)
        if not ok:
            print("❌ Cannot reach!")
            self._go_home()
            return False
        self._hold(150)
        # Step 2 — align XY only, stay above
        # Stay 0.06m above cube — NO descending
        # This avoids pushing cube entirely
        print("\\n[2] Aligning XY above cube...")
        align    = obj_pos.copy()
        align[2] = obj_pos[2] + 0.06
        self.move_to(align, hand, tolerance=0.03)
        self._hold(150)
        # Step 3 — GRASP HERE before touching
        # Teleport triggers at this distance
        # Hand never contacts cube physically
        print("\\n[3] Grasping from above...")
        self.grasp_object(obj_name, hand)
        self._hold(200)
        # Step 4 — small skip (was step 3)
        print("\\n[4] Grasp confirmed!")'''

if OLD in content:
    content = content.replace(OLD, NEW)
    print("✅ Pick sequence fixed!")
else:
    print("❌ Pattern not found exactly")
    print("Trying flexible fix...")
    import re
    # Just change the tolerance on move_to obj_pos
    # and add grasp before it
    content = re.sub(
        r'# Step 3 — move down to object.*?self\._hold\(200\)',
        '''# Step 3 — GRASP before touching
        # Stay above, teleport grasp fires here
        print("\\n[3] Grasping from above...")
        align    = obj_pos.copy()
        align[2] = obj_pos[2] + 0.06
        self.move_to(align, hand, tolerance=0.03)
        self._hold(100)
        self.grasp_object(obj_name, hand)
        self._hold(200)''',
        content, flags=re.DOTALL)
    print("✅ Applied flexible fix!")

with open('ik_controller.py', 'w') as f:
    f.write(content)
