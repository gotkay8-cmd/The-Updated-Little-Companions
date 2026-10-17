import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import tkinter as tk
from game import App
from model import GameState

class RuntimeArtTests(unittest.TestCase):
    def test_startup_without_retired_assets(self):
        root=tk.Tk();root.withdraw()
        with TemporaryDirectory() as folder:
            state=GameState(Path(folder)/'save.json')
            try:
                with patch('game.GameState',return_value=state),patch.object(App,'set_global_tracking'):
                    app=App(root)
                for pet in ('Mochi','Maple','Clover','Pip'):
                    for motion in ('idle','pet','play','typing','click','sleep','toy'):
                        app.paint_pet(app.canvas,pet,180,360,reaction=motion,percent=100)
                root.update_idletasks()
                self.assertEqual(app.motion_art['Mochi']['idle'][0].height(),360)
                app.background.stop()
            finally:root.destroy()

if __name__=='__main__':unittest.main()
