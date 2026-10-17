import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from input_events import BackgroundInput
from game import App


class ActivityTests(unittest.TestCase):
    def test_repeated_input_does_not_restart_animation(self):
        for reaction in ('typing', 'click'):
            app = SimpleNamespace(reaction='idle', until=0, manual_sleep=False,
                                  animation_started=0, animation_offset=0)
            App.start_reaction(app, reaction, now=10)
            self.assertEqual(App.animation_frame(app, now=10.3), 2)
            App.start_reaction(app, reaction, now=10.3)
            self.assertEqual(app.animation_started, 10)
            self.assertEqual(App.animation_frame(app, now=10.5), 3)
            self.assertGreater(app.until,10.3)
            self.assertIn(reaction,app.input_animations)

    def test_local_interface_click_counts_without_background_tracking(self):
        counts = []
        app = SimpleNamespace(global_input=False, paused=False, dirty=False,
                              state=SimpleNamespace(activity=lambda count,kind:counts.append((count,kind))))
        App.local_click(app, None)
        self.assertEqual(counts, [(1, 'clicks')])
        app.global_input=True
        App.local_click(app, None)
        app.global_input=False
        app.paused=True
        App.local_click(app, None)
        self.assertEqual(counts, [(1, 'clicks')])

    def test_local_pet_interaction_does_not_double_count_press(self):
        counts=[]
        app=SimpleNamespace(global_input=False,last_activity=10,activity=lambda **kw:counts.append(kw),
                            start_reaction=lambda reaction:None,render_animals=lambda:None)
        App.interact(app,'pet',count=False)
        self.assertEqual(counts,[])
        App.interact(app,'pet')
        self.assertEqual(len(counts),1)

    def test_listener_runs_independently_and_shuts_down(self):
        listener=BackgroundInput()
        thread_ids=[]
        def listen():
            thread_ids.append(threading.get_ident())
            listener.started=True
            listener.ready.set()
            while not listener.stopping.wait(.01):
                listener.events.put('typing')
        with patch('input_events.sys.platform','win32'),patch.object(listener,'_listen',side_effect=listen):
            self.assertTrue(listener.start())
            # Simulate a blocked UI render while the listener continues.
            time.sleep(.08)
            self.assertTrue(listener.running)
            self.assertNotEqual(thread_ids[0],threading.get_ident())
            self.assertGreater(len(list(listener.drain())),0)
            listener.stop()
            self.assertFalse(listener.running)
            self.assertEqual(list(listener.drain()),[])


if __name__=='__main__':unittest.main()
