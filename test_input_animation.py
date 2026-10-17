import unittest
from input_animation import InputAnimation

class InputAnimationTests(unittest.TestCase):
    def test_typing_advances_once_per_key_and_stops_without_input(self):
        a=InputAnimation('typing')
        a.event(1)
        self.assertEqual(a.frame(1),1)
        self.assertEqual(a.frame(1.5),1)
        a.event(2,3)
        self.assertEqual(a.frame(2),4)
        self.assertEqual(a.frame(3),4)

    def test_click_speed_follows_input_intervals(self):
        fast=InputAnimation('click');slow=InputAnimation('click')
        fast.event(0);fast.event(.2)
        slow.event(0);slow.event(1)
        self.assertAlmostEqual(fast.period,.2)
        self.assertAlmostEqual(slow.period,1)
        f0,s0=fast.phase,slow.phase
        fast.frame(.3);slow.frame(1.1)
        self.assertGreater(fast.phase-f0,slow.phase-s0)

    def test_rate_change_does_not_restart_cycle(self):
        a=InputAnimation('click');a.event(0);a.frame(.15)
        before=a.phase;a.event(.15)
        self.assertEqual(a.phase,before)
        a.frame(5)
        self.assertEqual(a.phase,a.target)
        phase=a.phase;a.frame(10)
        self.assertEqual(a.phase,phase)

    def test_event_timestamps_survive_batched_delivery(self):
        a=InputAnimation('click')
        for t in (1,1.4,1.8):a.event(t)
        self.assertAlmostEqual(a.period,.4)

if __name__=='__main__':unittest.main()
