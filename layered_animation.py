"""Approved per-frame artwork. Outfits remain separate from the bare pet."""
from pathlib import Path
from functools import lru_cache
import json


@lru_cache(maxsize=4)
def manifest(art_dir):
    path=Path(art_dir)/'layered-motions/manifest.json'
    return json.loads(path.read_text()) if path.is_file() else {'records':{}}


def motion_key(motion='idle',walking=None,running=None):
    return 'run-'+running if running else 'walk-'+walking if walking else {'toy':'play'}.get(motion,motion)


def sequence(art_dir,pet,motion='idle',walking=None,running=None):
    return manifest(str(art_dir))['records'].get(pet.lower()+'/'+motion_key(motion,walking,running))


def motion_frame(art_dir,pet,motion,index,walking=None,running=None,facing=0):
    if facing and not walking and not running:
        direction={45:'right',90:'right',135:'up',180:'up',225:'left',270:'left',315:'down'}.get(facing,'down')
        return motion_frame(art_dir,pet,'idle',0,walking=direction) or base_frame(art_dir,pet,direction,0)
    info=sequence(art_dir,pet,motion,walking,running)
    if not info:return None
    return Path(art_dir)/'layered-motions'/pet.lower()/motion_key(motion,walking,running)/'base'/f'frame-{index % info["frames"]:02}.png'


def idle_index(art_dir,pet,seconds):
    info=sequence(art_dir,pet,'idle')
    durations=info.get('durations_ms',[info['duration_ms']]*info['frames'])
    elapsed=(seconds*1000)%sum(durations)
    for i,duration in enumerate(durations):
        if elapsed<duration:return i
        elapsed-=duration
    return 0


def timing(art_dir,pet,motion='idle',walking=None,running=None):
    if walking in ('left','right'):return walking_timing(walking)
    info=sequence(art_dir,pet,motion,walking,running)
    if info:return info['frames'],info['duration_ms']/1000
    return (8,.09) if running else (4,.18 if walking else .14)


def preview_timing(art_dir,pet,label):
    if label=='Turn around':return 8,.24
    if label.startswith('Walk '):return timing(art_dir,pet,walking=label.split()[1])
    if label.startswith('Run '):return timing(art_dir,pet,running=label.split()[1])
    from outfit_preview import REACTIONS
    return timing(art_dir,pet,REACTIONS.get(label,'idle'))


def walking_timing(direction):
    return (9, .09) if direction in ('left', 'right') else (16, .18)


def base_frame(art_dir, pet, walking, index):
    if walking not in ('left', 'right'):
        return None
    path = Path(art_dir)/'layered-walk'/pet.lower()/walking/'base'/f'frame-{index % 9 + 1:02}.png'
    return path if path.is_file() else None


def layers(art_dir, data, pet, base_path):
    base_path=Path(base_path)
    root = Path(art_dir)/'layered-walk'
    try:
        relative = Path(base_path).relative_to(root)
    except ValueError:
        root=Path(art_dir)/'layered-motions'
        try:relative=base_path.relative_to(root)
        except ValueError:return None
    if len(relative.parts) != 4 or relative.parts[0] != pet.lower():
        return None
    from wardrobe import CATALOG
    from accessory_layers import COLLARS
    slots = data.get('wardrobe', {}).get(pet, {})
    owned = data.get('items', [])
    result = []
    for slot in ('outfit', 'neck', 'charm', 'head'):
        # Keep the outfit equipped, but show the bare body when walking away.
        if slot == 'outfit' and relative.parts[1] == 'walk-up':
            continue
        item = slots.get(slot)
        info = CATALOG.get(item, {})
        if item not in owned or info.get('slot') != slot or info.get('pet') not in (None, pet):
            continue
        if slot == 'charm' and (slots.get('neck') not in COLLARS or slots.get('neck') not in owned):
            continue
        slug = item.lower().removeprefix(pet.lower()+' ').removesuffix(' outfit').replace(' ', '-')
        if root.name=='layered-motions':
            record=manifest(str(art_dir))['records'][relative.parts[0]+'/'+relative.parts[1]]
            if slug not in record['outfits']+record['accessories']:continue
        path = root/relative.parts[0]/relative.parts[1]/'layers'/slug/base_path.name.replace('frame-', 'layer-')
        if path.is_file():
            result.append(path)
    return result
