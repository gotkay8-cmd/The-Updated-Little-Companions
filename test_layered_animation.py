import unittest
from pathlib import Path
from wardrobe import CATALOG, outfit_sprite
from wardrobe_model import WardrobeDraft
from accessory_layers import layer_paths
from outfit_preview import Playback
from layered_animation import manifest, timing, preview_timing
from copy import deepcopy

ART = Path(__file__).resolve().parent/'assets/v5'


class LayeredWalkingTests(unittest.TestCase):
    def test_stationary_frames_share_a_level_contact_anchor(self):
        from png_scaling import read_rgba
        for key,info in manifest(str(ART))['records'].items():
            if key.split('/')[1] not in ('idle','pet','play','click','sleep','typing'):continue
            self.assertEqual(info['ground_anchor'],[180,330])
            for i in range(info['frames']):
                path=ART/'layered-motions'/key/'base'/f'frame-{i:02}.png'
                w,h,rows=read_rgba(path)
                self.assertEqual((w,h),(360,360))
                floor=max(y for y,row in enumerate(rows) if any(row[x*4+3]>128 for x in range(120,240)))
                self.assertEqual(floor,330,(key,i,floor))

    def test_all_installed_sequences_reach_every_frame(self):
        for key,info in manifest(str(ART))['records'].items():
            pet,motion=key.split('/')
            label=('Walk '+motion[5:] if motion.startswith('walk-') else
                   'Run '+motion[4:] if motion.startswith('run-') else
                   {'idle':'Idle','pet':'Petting','play':'Playing','typing':'Typing','click':'Clicking','sleep':'Sleeping'}[motion])
            playback=Playback(lambda m:preview_timing(ART,pet.title(),m))
            playback.select(label)
            self.assertEqual(playback.count,info['frames'])
            draft=WardrobeDraft({},pet.title())
            bases=[]
            for frame in range(info['frames']):
                paths=draft.paths(ART,label,frame)
                self.assertTrue(all(p.is_file() for p in paths),paths)
                bases.append(paths[0])
            self.assertEqual(len(set(bases)),info['frames'],key)

    def test_running_outfit_visible_unfinished_charm_hidden(self):
        slots=dict(outfit='Clover Garden Outfit',neck='Meadow Collar',head='Cozy Beret',charm='Acorn Charm')
        data={'items':list(slots.values()),'wardrobe':{'Clover':slots}}
        before=deepcopy(data)
        for i in range(10):
            base=outfit_sprite(ART,data,'Clover','idle',i,running='right')
            layers=layer_paths(ART,data,'Clover',base)
            self.assertEqual([p.parent.name for p in layers],['garden','meadow-collar','cozy-beret'])
        self.assertEqual(data,before)

    def test_every_outfit_resolves_every_installed_motion_frame(self):
        for item, info in CATALOG.items():
            if info['slot'] != 'outfit':continue
            pet=info['pet']
            draft=WardrobeDraft({'wardrobe':{pet:{'outfit':item}}},pet)
            for key, record in manifest(str(ART))['records'].items():
                if not key.startswith(pet.lower()+'/'):continue
                motion=key.split('/')[1]
                label=('Walk '+motion[5:] if motion.startswith('walk-') else
                       'Run '+motion[4:] if motion.startswith('run-') else
                       {'idle':'Idle','pet':'Petting','play':'Playing','typing':'Typing','click':'Clicking','sleep':'Sleeping'}[motion])
                for i in range(record['frames']):
                    paths=draft.paths(ART,label,i)
                    self.assertEqual(len(paths),1 if motion=='walk-up' else 2,(item,key,i,paths))
                    self.assertTrue(all(p.is_file() for p in paths),paths)
                    if motion!='walk-up':
                        self.assertEqual(paths[1].name,f'layer-{i:02}.png')

    def test_walk_up_hides_only_clothing_and_preserves_equipment(self):
        for pet in ('Mochi','Maple','Clover','Pip'):
            outfit=next(i for i,v in CATALOG.items() if v['slot']=='outfit' and v['pet']==pet)
            slots=dict(outfit=outfit,neck='Meadow Collar',head='Cozy Beret')
            data={'items':list(slots.values()),'wardrobe':{pet:slots}}
            before=deepcopy(data)
            for i in range(16):
                base=outfit_sprite(ART,data,pet,'idle',i,walking='up')
                paths=layer_paths(ART,data,pet,base)
                self.assertEqual([p.parent.name for p in paths],['meadow-collar','cozy-beret'])
            base=outfit_sprite(ART,data,pet,'idle',0,walking='down')
            self.assertEqual(len(layer_paths(ART,data,pet,base)),3)
            self.assertEqual(data,before)

    def test_polished_overalls_and_accessories_have_all_frames(self):
        for pet in ('Mochi','Maple','Clover','Pip'):
            outfit=next(i for i in CATALOG if i.startswith(pet) and 'Overalls' in i)
            slots=dict(outfit=outfit,neck='Meadow Collar',charm='Acorn Charm',head='Cozy Beret')
            data={'items':list(slots.values()),'wardrobe':{pet:slots}}
            for i in range(8):
                base=outfit_sprite(ART,data,pet,'typing',i)
                layers=layer_paths(ART,data,pet,base)
                self.assertEqual(len(layers),4)
                self.assertTrue(all(p.is_file() for p in layers))

    def test_every_outfit_frame_in_both_directions(self):
        for item, info in CATALOG.items():
            if info['slot'] != 'outfit':
                continue
            pet = info['pet']
            draft = WardrobeDraft({'wardrobe': {pet: {'outfit': item}}}, pet)
            for direction in ('left', 'right'):
                for index in range(9):
                    paths = draft.paths(ART, 'Walk '+direction, index)
                    self.assertEqual(len(paths), 2, (item, direction, index))
                    self.assertTrue(all(p.is_file() for p in paths), paths)
                    self.assertIn('base', paths[0].parts)
                    self.assertIn('layers', paths[1].parts)

    def test_owned_layer_order_and_unowned_items(self):
        for pet in ('Mochi', 'Maple', 'Clover', 'Pip'):
            outfit = next(i for i,v in CATALOG.items() if v['pet']==pet)
            slots = dict(outfit=outfit, neck='Meadow Collar', charm='Acorn Charm', head='Cozy Beret')
            data = {'items': list(slots.values()), 'wardrobe': {pet: slots}}
            base = outfit_sprite(ART, data, pet, 'idle', 8, walking='right')
            paths = layer_paths(ART, data, pet, base)
            self.assertEqual(len(paths), 4)
            self.assertEqual([p.parent.name for p in paths[1:]], ['meadow-collar','acorn-charm','cozy-beret'])
            self.assertTrue(all(p.name=='layer-09.png' for p in paths))
            data['items'] = []
            self.assertEqual(layer_paths(ART, data, pet, base), [])
            self.assertEqual(outfit_sprite(ART, data, pet, 'idle', 8, walking='right'), base)

    def test_nine_frames_and_wrap(self):
        playback = Playback()
        playback.showcase = False
        playback.select('Walk right')
        frames = []
        for _ in range(9):
            frames.append(playback.frame)
            playback.step()
        self.assertEqual(frames, list(range(9)))
        self.assertEqual(playback.frame, 0)
        self.assertEqual(playback.interval, .09)
        a = outfit_sprite(ART, {}, 'Mochi', 'idle', 0, walking='right')
        b = outfit_sprite(ART, {}, 'Mochi', 'idle', 9, walking='right')
        self.assertEqual(a, b)


if __name__ == '__main__':
    unittest.main()
