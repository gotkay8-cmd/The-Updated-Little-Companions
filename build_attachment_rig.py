"""Convert legacy placement into editable sockets; accessory art stays shared.

Run with Pillow when authoring art. The game itself needs only Python/Tk.
Placement is metadata, never a new accessory animation or outfit combination.
"""
import json
from pathlib import Path
from PIL import Image
from accessory_layers import MODULAR, layer_key
from accessory_index import INDEX

ROOT = Path(__file__).parent / 'assets' / 'v5'

def main():
    frames = {}
    for base in sorted(ROOT.rglob('*.png')):
        relative = base.relative_to(ROOT).as_posix()
        if relative.startswith(('accessory-', 'item-', 'button-', 'cursor-', 'toy-')):
            continue
        pet = next((p for p in ('mochi', 'maple', 'clover', 'pip')
                    if relative.startswith(p+'_') or relative.startswith(p+'-')
                    or relative.startswith('outfits/'+p+'/')), None)
        if not pet or 'icon' in relative: continue
        key = layer_key(ROOT, base)
        sockets = {}
        for item, socket in (('Meadow Collar','neck'), ('Daisy Ear Bow','ear'),
                             ('Cozy Beret','crown')):
            slug = item.lower().replace(' ', '-')
            path = ROOT / INDEX.get((slug,key), 'accessory-layers/'+slug+'/'+key+'.png')
            if not path.is_file(): continue
            bbox = Image.open(path).getbbox()
            if bbox:
                x,y,r,b = bbox
                sockets[socket] = dict(x=(x+r)/2, y=(y+b)/2, width=r-x, height=b-y)
        if not sockets: continue
        name = base.stem
        angle = int(name.split('-')[-1]) if 'turn-' in name else None
        rear = 'walk-up' in name or 'run-up' in name or angle in (135,180,225)
        side = 'left' in name or 'right' in name or angle in (90,270)
        sockets['view'] = 2 if rear else 1 if side else 0
        sockets['front_visible'] = not rear
        frames[relative] = sockets
    (ROOT/'attachment-rig.json').write_text(json.dumps({'version':1,'frames':frames},separators=(',',':')))
    print('Authored sockets for', len(frames), 'pet frames')

if __name__ == '__main__': main()
