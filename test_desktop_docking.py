import unittest
from desktop_overlay import docked_position

class DesktopDockingTests(unittest.TestCase):
    def test_contact_edge_matches_taskbar_at_every_scale(self):
        for scale in (.5,.75,1,1.25,1.5):
            for work in ((0,0,1920,1032),(-1920,0,0,1032),(0,-1080,1920,-48)):
                x,y=docked_position(work,round(440*scale),scale,work[0]+80)
                self.assertEqual(y+round(331*scale),work[3])
                self.assertGreaterEqual(x,work[0])
                self.assertLessEqual(x+round(440*scale),work[2])
