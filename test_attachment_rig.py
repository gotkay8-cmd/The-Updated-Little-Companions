"""Geometry and equipment regressions for the shared attachment renderer."""
import unittest
from pathlib import Path
from accessory_layers import MODULAR, equip_accessory, accessory_equipped, layer_paths
from attachment_rig import rig, fitted_layer
from png_scaling import read_rgba

ROOT=Path(__file__).parent/'assets'/'v5'

class Attachments(unittest.TestCase):
    def test_all_sockets_are_inside_the_frame(self):
        frames=rig(str(ROOT))
        self.assertGreater(len(frames),2000)
        for name,sockets in frames.items():
            self.assertTrue((ROOT/name).is_file(),name)
            for key in ('ear','crown','neck'):
                if key not in sockets:continue
                socket=sockets[key]
                self.assertTrue(0<=socket['x']<=360,name)
                self.assertTrue(0<=socket['y']<=310,name)
                self.assertGreater(socket['width'],0,name)

    def test_charm_requires_collar_and_follows_removal(self):
        data={'items':list(MODULAR),'wardrobe':{}}
        equip_accessory(data,'Mochi','Acorn Charm')
        self.assertFalse(accessory_equipped(data,'Mochi'))
        equip_accessory(data,'Mochi','Meadow Collar')
        equip_accessory(data,'Mochi','Acorn Charm')
        self.assertEqual(len(accessory_equipped(data,'Mochi')),2)
        equip_accessory(data,'Mochi','Meadow Collar')
        self.assertFalse(accessory_equipped(data,'Mochi'))

    def test_bows_fit_costume_headwear(self):
        data={'items':list(MODULAR),'wardrobe':{'Mochi':{'outfit':'Mochi Little Witch Outfit'}}}
        equip_accessory(data,'Mochi','Daisy Ear Bow')
        self.assertIn('Daisy Ear Bow',accessory_equipped(data,'Mochi'))
        self.assertIn('painted-in',equip_accessory(data,'Mochi','Cozy Beret'))

    def test_shared_parts_render_across_pets_outfits_and_views(self):
        for pet in ('mochi','maple','clover','pip'):
            for base in sorted((ROOT/'outfits'/pet).rglob('*.png')):
                frame=base.stem
                if frame not in ('idle-0','sleep-1','walk-left-2','walk-up-0','run-right-3','turn-180'):continue
                for item,definition in MODULAR.items():
                    result=fitted_layer(str(ROOT),str(base),item.lower().replace(' ','-'),definition['kind'])
                    if frame in ('walk-up-0','turn-180') and definition['kind'] in ('charm','bandana'):
                        self.assertIsNone(result)
                    elif result:
                        w,h,rows=read_rgba(str(result))
                        self.assertEqual((w,h),(360,310))
                        self.assertTrue(any(row[x]>0 for row in rows for x in range(3,len(row),4)),(pet,frame,item))

if __name__=='__main__':unittest.main()
