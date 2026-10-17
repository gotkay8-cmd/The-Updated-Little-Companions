import unittest
from cursor_reaction import CursorReaction

class CursorTests(unittest.TestCase):
    def test_right_cursor_raises_only_screen_right_paw(self):
        c=CursorReaction();seen=[]
        for i in range(20):
            c.update('toy',260,i*.1);seen.append(c.frame)
        self.assertEqual(seen[:3],[4,5,6])
        self.assertTrue(set(seen)<={4,5,6})

    def test_crossing_retracts_before_raising_other_paw(self):
        c=CursorReaction()
        for i in range(4):c.update('toy',90,i*.1)
        seen=[]
        for i in range(4,11):
            c.update('toy',260,i*.1);seen.append(c.frame)
        self.assertEqual(seen[:5],[1,0,4,5,6])

    def test_pet_lean_and_center_hysteresis(self):
        c=CursorReaction()
        for i in range(6):c.update('pet',260,i*.1)
        self.assertEqual(c.frame,4)
        c.update('pet',179,.7)
        self.assertEqual(c.frame,4)
        for i in range(8,18):c.update('pet',80,i*.1)
        self.assertEqual(c.frame,3)
        c.update(None,80,2)
        self.assertIsNone(c.zone)

if __name__=='__main__':unittest.main()
