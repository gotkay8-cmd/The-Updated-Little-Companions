import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
from wardrobe_model import WardrobeDraft
from wardrobe import CATALOG
from model import GameState, price_for


def data():
    return {'items': [], 'wardrobe': {'Mochi': {}}, 'coins': 500, 'moonstones': 500}


class FittingRoomTests(unittest.TestCase):
    def test_browsing_is_a_draft_and_unowned_items_cannot_be_worn(self):
        original = data()
        before = deepcopy(original)
        draft = WardrobeDraft(original, 'Mochi')
        draft.cycle('outfit', 1, original)
        self.assertEqual(original, before)
        self.assertTrue(draft.missing(original))
        self.assertFalse(draft.apply(original))
        self.assertEqual(original, before)

    def test_purchase_uses_existing_currency_then_applies(self):
        original = data()
        draft = WardrobeDraft(original, 'Mochi')
        draft.cycle('outfit', 1, original)
        item = draft.slots['outfit']
        state = GameState.__new__(GameState)
        state.data = original
        currency, cost = price_for(item)
        before = original[currency]
        state.buy(item)
        self.assertEqual(original[currency], before - cost)
        self.assertEqual(original['wardrobe']['Mochi'], {})
        self.assertTrue(draft.apply(original))
        self.assertEqual(original['wardrobe']['Mochi']['outfit'], item)
        state.buy(item)
        self.assertEqual(original[currency], before - cost)

    def test_collar_removal_clears_charm(self):
        original = data()
        draft = WardrobeDraft(original, 'Mochi')
        draft.slots = {'neck': 'Meadow Collar', 'charm': 'Acorn Charm'}
        draft.cycle('neck', -1, original)
        self.assertNotIn('charm', draft.slots)
        self.assertEqual(draft.options('charm', original), [None])

    def test_costume_hat_conflict_preserves_bow(self):
        draft = WardrobeDraft(data(), 'Mochi')
        draft.slots = {'outfit': 'Mochi Little Witch Outfit', 'head': 'Daisy Ear Bow'}
        draft.normalize()
        self.assertEqual(draft.slots['head'], 'Daisy Ear Bow')
        self.assertNotIn('Cozy Beret', draft.options('head', data()))

    def test_expired_items_remain_available_only_if_owned(self):
        original = data()
        draft = WardrobeDraft(original, 'Mochi')
        with patch('model.shop_available', return_value=False):
            self.assertEqual(draft.options('outfit', original), [None])
            original['items'].append('Mochi Little Witch Outfit')
            self.assertIn('Mochi Little Witch Outfit', draft.options('outfit', original))

    def test_model_has_art_for_every_pet_and_motion(self):
        root = Path(__file__).parent / 'assets' / 'v5'
        from model import PETS
        from outfit_preview import MOTIONS, Playback
        for pet in PETS:
            draft = WardrobeDraft(data(), pet)
            for motion in MOTIONS:
                playback = Playback()
                playback.select(motion)
                for frame in range(playback.count):
                    for path in draft.paths(root, motion, frame):
                        self.assertTrue(path.is_file(), str(path))

    def test_insufficient_funds_do_not_unlock_or_apply(self):
        original = data()
        original['moonstones'] = 0
        state = GameState.__new__(GameState)
        state.data = original
        draft = WardrobeDraft(original, 'Mochi')
        draft.cycle('outfit', 1, original)
        state.buy(draft.slots['outfit'])
        self.assertFalse(draft.apply(original))
        self.assertEqual(original['items'], [])
        self.assertEqual(original['wardrobe']['Mochi'], {})

    def test_fitting_room_controls_buy_wear_reset_and_close(self):
        import tkinter as tk
        from types import SimpleNamespace
        from cozy_ui import CozyButton
        from wardrobe_fitting import FittingRoom
        root = tk.Tk()
        root.withdraw()
        try:
            state = GameState.__new__(GameState)
            state.data = data()
            state.data.update(pet='Mochi', names={p:p for p in ('Mochi','Maple','Clover','Pip')})
            content = tk.Frame(root, bg='#fff8eb')
            content.pack()
            app = SimpleNamespace(root=root, content=content, state=state,
                                  heading_font='Arial', body_font='Arial',
                                  art_dir=Path(__file__).parent/'assets'/'v5',
                                  notice=tk.StringVar(root), save=lambda:None,
                                  choose_wardrobe=lambda p:None,
                                  button=lambda parent,text,command,active:CozyButton(parent,text,command,('Arial',10),active).pack())
            room = FittingRoom(app)
            root.update_idletasks()
            room.cycle('outfit', 1)
            self.assertTrue(room.wear.disabled)
            room.buy('outfit')
            self.assertFalse(room.wear.disabled)
            room.apply()
            worn = dict(state.data['wardrobe']['Mochi'])
            room.cycle('outfit', 1)
            room.reset()
            self.assertEqual(room.draft.slots, worn)
            room.motion('Walk left')
            self.assertTrue(room.canvas.find_withtag('pet'))
            room.frame.destroy()
            self.assertTrue(room.closed)
            print('Fitting room requested size:', content.winfo_reqwidth(), content.winfo_reqheight())
        finally:
            root.destroy()


if __name__ == '__main__':
    unittest.main()
