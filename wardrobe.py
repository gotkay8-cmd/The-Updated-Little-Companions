"""Complete drawn outfits shared by the room and native desktop renderer."""
from pathlib import Path
OUTFITS={'Mochi':'Mochi Cloud Outfit','Maple':'Maple Trail Outfit',
         'Clover':'Clover Garden Outfit','Pip':'Pip Woodland Outfit'}
CATALOG={name:dict(pet=pet,slot='outfit',price=90) for pet,name in OUTFITS.items()}

NEW_OUTFITS={'Mochi': ['Mochi Rose Knit Outfit', 'Mochi Bluebell Overalls Outfit', 'Mochi Lavender Pajamas Outfit'], 'Maple': ['Maple Honey Knit Outfit', 'Maple Denim Overalls Outfit', 'Maple Sky Pajamas Outfit'], 'Clover': ['Clover Meadow Knit Outfit', 'Clover Petal Overalls Outfit', 'Clover Chamomile Pajamas Outfit'], 'Pip': ['Pip Rust Knit Outfit', 'Pip Forest Overalls Outfit', 'Pip Acorn Pajamas Outfit']}
for pet,names in NEW_OUTFITS.items():
    for name in names:CATALOG[name]=dict(pet=pet,slot='outfit',price=90,variant=name.lower().replace(' ','-'))
HALLOWEEN_OUTFITS={
    'Mochi':['Mochi Little Witch Outfit','Mochi Pumpkin Outfit'],
    'Maple':['Maple Cozy Vampire Outfit','Maple Harvest Scarecrow Outfit'],
    'Clover':['Clover Candy Corn Outfit','Clover Woodland Fairy Outfit'],
    'Pip':['Pip Little Bat Outfit','Pip Moon Wizard Outfit']}
for pet,names in HALLOWEEN_OUTFITS.items():
    for name in names:CATALOG[name]=dict(pet=pet,slot='outfit',price=90,variant=name.lower().replace(' ','-'),season='Halloween')
OUTFIT_PRICES={'Common':10,'Rare':20,'Epic':40,'Legendary':60}
for pet,name in OUTFITS.items():CATALOG[name].update(rarity='Common',price=10)
for pet,names in NEW_OUTFITS.items():
    for name,tier in zip(names,('Rare','Epic','Epic')):CATALOG[name].update(rarity=tier,price=OUTFIT_PRICES[tier])
for names in HALLOWEEN_OUTFITS.values():
    for name in names:CATALOG[name].update(rarity='Legendary',price=60)
from accessory_layers import MODULAR,accessory_equipped
for name,info in MODULAR.items():CATALOG[name]=dict(info,pet=None,price={'Common':20,'Uncommon':40,'Rare':70,'Epic':110}[info['rarity']])
SLOTS=('outfit','head','neck','charm')
MOTIONS=('idle','typing','click','pet','play','sleep','toy')
DIRECTIONS=('left','right','down','up')
OUTFIT_ANGLES=(0,45,90,135,180,225,270,315)
LEGACY_DESIGNS={
 'Mochi':('Moon Collar','Rose Collar','Dream Bandana','Cloud Vest','Star Pajamas'),
 'Maple':('Sky Collar','Paw Collar','Scout Bandana','Trail Vest','Paw Pajamas'),
 'Clover':('Daisy Collar','Meadow Collar','Petal Bandana','Garden Vest','Daisy Pajamas'),
 'Pip':('Acorn Collar','Forest Collar','Explorer Bandana','Woodland Vest','Acorn Pajamas')}
RETIRED={pet+' '+name:dict(pet=pet,price=(25,25,35,65,65)[i],outfit=i>=3)
         for pet,names in LEGACY_DESIGNS.items() for i,name in enumerate(names)}
RETIRED.update({name:dict(pet=None,price=30,outfit=False) for name in ('Bow','Scarf')})
def slug(item):return item.lower().replace(' ','-')
def available(item,pet):return item in CATALOG and CATALOG[item]['pet'] in (None,pet)
def equipped(data,pet):
    item=data.get('wardrobe',{}).get(pet,{}).get('outfit')
    return ([item] if available(item,pet) and item in data.get('items',[]) and CATALOG[item]['slot']=='outfit' else [])+accessory_equipped(data,pet)
def outfit_sprite(art_dir,data,pet,motion,index,walking=None,facing=0,running=None):
    """Return a complete pet frame, never an overlay or a base sprite."""
    worn=[i for i in equipped(data,pet) if CATALOG[i]['slot']=='outfit']
    if not worn:return None
    name=(f'run-{running}-{index%8}' if running else
          f'walk-{walking}-{index%walk_frame_count(walking)}' if walking else
          f'turn-{facing}' if facing in OUTFIT_ANGLES and facing else
          f'{motion}-{index%4}')
    from approved_art import approved_sprite
    approved = approved_sprite(art_dir, data, pet, name)
    if approved is not None:return approved
    directory=Path(art_dir)/'outfits'/pet.lower()
    variant=CATALOG[worn[0]].get('variant')
    if variant:directory=directory/variant
    return directory/(name+'.png')
def turn_angles(data,pet):
    return OUTFIT_ANGLES if any(CATALOG[i]['slot']=='outfit' for i in equipped(data,pet)) else (0,90,135,180,225,270)
def migrate_clothing(data):
    """Upgrade one old outfit per pet; refund other retired pieces and spares."""
    items=data.get('items')
    if not isinstance(items,list):return ''
    retired=[item for item in dict.fromkeys(items) if item in RETIRED]
    if not retired:return ''
    wardrobe=data.get('wardrobe',{})
    if not isinstance(wardrobe,dict):wardrobe={}
    accessory=data.get('accessory',{})
    if not isinstance(accessory,dict):accessory={}
    duplicates=data.get('duplicates',{})
    if not isinstance(duplicates,dict):duplicates={}
    credit=0;upgrades=[];consumed=set()
    for pet,new in OUTFITS.items():
        slots=wardrobe.get(pet,{})
        if not isinstance(slots,dict):slots={}
        previous=list(slots.values())+[accessory.get(pet,'')]
        candidates=[i for i in retired if RETIRED[i]['pet']==pet and RETIRED[i]['outfit']]
        if candidates and new not in items:
            old=next((i for i in candidates if i in previous),candidates[0])
            consumed.add(old);items.append(new);upgrades.append(new)
            if any(i in retired for i in previous):slots['outfit']=new
        wardrobe[pet]={slot:item for slot,item in slots.items() if item not in RETIRED}
        if accessory.get(pet) in RETIRED:accessory[pet]=''
    for item in retired:
        if item not in consumed:credit+=RETIRED[item]['price']
        count=duplicates.pop(item,0)
        if type(count) is int and count>0:credit+=10*count
    data['items']=[item for item in items if item not in RETIRED]
    data['wardrobe']=wardrobe;data['accessory']=accessory;data['duplicates']=duplicates
    data['coins']+=credit
    return f'Wardrobe updated: {len(upgrades)} complete outfit(s) upgraded; {credit} leaves returned for retired clothing and spares.'


def walk_frame_count(direction):return 4

def owned_wearables(data,pet=None):
    return [item for item,info in CATALOG.items() if item in data.get('items',[]) and (pet is None or info['pet'] in (None,pet))]
