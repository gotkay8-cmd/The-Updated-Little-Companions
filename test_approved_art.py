import unittest
from pathlib import Path
from copy import deepcopy
from approved_art import approved_slots
from wardrobe import outfit_sprite
from accessory_layers import layer_paths

ART = Path(__file__).parent / 'assets/v5'

class ApprovedArtTests(unittest.TestCase):
    def test_all_supported_poses_resolve_without_duplicate_accessories(self):
        for pet in ('Mochi', 'Maple', 'Clover', 'Pip'):
            slots = approved_slots(pet)
            data = {'items': list(slots.values()), 'wardrobe': {pet: slots}}
            for motion in ('idle', 'play', 'pet', 'typing', 'click', 'sleep', 'toy'):
                for index in range(4):
                    path = outfit_sprite(ART, data, pet, motion, index)
                    self.assertTrue(path.is_file(), path)
                    self.assertIn('approved', path.parts)
                    self.assertEqual(layer_paths(ART, data, pet, path), [])
            for direction in ('left', 'right'):
                for index in range(8):
                    path = outfit_sprite(ART, data, pet, 'idle', index, running=direction)
                    self.assertTrue(path.is_file(), path)
            for direction in ('left', 'right', 'up', 'down'):
                for index in range(4):
                    self.assertTrue(outfit_sprite(ART, data, pet, 'idle', index, walking=direction).is_file())

    def test_changing_or_not_owning_accessory_uses_customizable_art(self):
        slots = approved_slots('Mochi')
        original = {'items': list(slots.values()), 'wardrobe': {'Mochi': slots}}
        for change in ('removed', 'changed', 'unowned'):
            data = deepcopy(original)
            if change == 'removed':data['wardrobe']['Mochi'].pop('head')
            if change == 'changed':
                data['items'].append('Cozy Beret')
                data['wardrobe']['Mochi']['head'] = 'Cozy Beret'
            if change == 'unowned':data['items'].remove('Acorn Charm')
            path = outfit_sprite(ART, data, 'Mochi', 'play', 2)
            self.assertNotIn('approved', path.parts)
            self.assertTrue(path.is_file())

if __name__ == '__main__':unittest.main()
