"""Independent accessory equipment and pre-fitted transparent sprite layers."""
from pathlib import Path
from hashlib import sha1
MODULAR={
 'Daisy Ear Bow':dict(slot='head',rarity='Uncommon',kind='bow'),
 'Cozy Beret':dict(slot='head',rarity='Rare',kind='hat'),
 'Meadow Collar':dict(slot='neck',rarity='Common',kind='collar'),
 'Cloud Bandana':dict(slot='neck',rarity='Uncommon',kind='bandana'),
 'Acorn Charm':dict(slot='charm',rarity='Uncommon',kind='charm'),
 'Candy Corn Bow':dict(slot='head',rarity='Rare',kind='bow',season='Halloween'),
 'Tiny Witch Hat':dict(slot='head',rarity='Epic',kind='hat',season='Halloween'),
 'Midnight Collar':dict(slot='neck',rarity='Rare',kind='collar',season='Halloween'),
 'Pumpkin Bell':dict(slot='charm',rarity='Rare',kind='charm',season='Halloween'),
 'Bat Charm':dict(slot='charm',rarity='Epic',kind='charm',season='Halloween')}
COLLARS=('Meadow Collar','Midnight Collar')
# These costumes already contain a hat/head ornament; avoid overlapping headwear.
HEAD_CONFLICTS=('Mochi Little Witch Outfit','Mochi Pumpkin Outfit','Maple Harvest Scarecrow Outfit','Clover Candy Corn Outfit','Clover Woodland Fairy Outfit','Pip Moon Wizard Outfit')

def head_conflict(slots,item):
    # Ear decorations still attach on costumes with painted-in hats.
    return MODULAR[item]['kind']=='hat' and slots.get('outfit') in HEAD_CONFLICTS
def accessory_equipped(data,pet):
    slots=data.get('wardrobe',{}).get(pet,{})
    return [slots[s] for s in ('neck','charm','head') if slots.get(s) in MODULAR and slots[s] in data.get('items',[]) and not (s=='charm' and slots.get('neck') not in COLLARS) and not(s=='head' and head_conflict(slots,slots[s]))]
def equip_accessory(data,pet,item):
    if item not in data.get('items',[]):return 'Own this accessory before wearing it.'
    slots=data.setdefault('wardrobe',{}).setdefault(pet,{})
    slot=MODULAR[item]['slot']
    if slots.get(slot)==item:
        slots.pop(slot)
        if slot=='neck':slots.pop('charm',None)
        return 'Removed '+item+'.'
    if slot=='head' and head_conflict(slots,item):return 'This outfit has a painted-in hat. Ear bows can still be worn with it.'
    if slot=='charm' and slots.get('neck') not in COLLARS:return 'Equip the Meadow Collar or Midnight Collar first.'
    slots[slot]=item
    if slot=='neck' and item not in COLLARS:slots.pop('charm',None)
    return 'Wearing '+item+'.'
def layer_key(art_dir,base_path):
    return sha1(Path(base_path).relative_to(Path(art_dir)).as_posix().encode()).hexdigest()[:16]
def layer_paths(art_dir,data,pet,base_path):
    from attachment_rig import attachment_paths
    attached=attachment_paths(art_dir,pet,base_path,accessory_equipped(data,pet),MODULAR)
    if attached is not None:return attached
    key=layer_key(art_dir,base_path)
    try:
        from accessory_index import INDEX
    except ImportError:INDEX={}
    result=[]
    for item in accessory_equipped(data,pet):
        slug=item.lower().replace(' ','-')
        relative=INDEX.get((slug,key),'accessory-layers/'+slug+'/'+key+'.png')
        path=Path(art_dir)/relative
        if path.is_file():result.append(path)
    return result
