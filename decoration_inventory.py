"""Copy counts and room reservations. Each placed instance spends one owned copy."""
from collections import Counter
from uuid import uuid4

def item_name(instance):return instance.split('::',1)[0] if isinstance(instance,str) else ''
def total_owned(data,item):
    return (1+data.get('duplicates',{}).get(item,0)) if item in data.get('items',[]) else 0

def room_placements(data):
    """Current-room lists override their saved snapshots; never double count them."""
    rooms={}
    for pet,by_room in data.get('room_decorations',{}).items():
        for room,items in by_room.items():rooms[pet,room]=list(items)
    for pet,room in data['pet_rooms'].items():rooms[pet,room]=list(data['decorations'][pet])
    return rooms

def reservations(data):
    rooms=room_placements(data)
    for pet,by_room in data.get('room_cushions',{}).items():
        if not isinstance(by_room,dict):continue
        for room,seat in by_room.items():
            if seat in data.get('items',[]):
                values=rooms.setdefault((pet,room),[])
                if seat not in [item_name(i) for i in values]:values.append(seat)
    return rooms

def used_count(data,item):return sum(item_name(i)==item for items in reservations(data).values() for i in items)
def free_count(data,item):return max(0,total_owned(data,item)-used_count(data,item))
def collection_counts(data,item):
    from wardrobe import CATALOG,equipped
    from model import THEMES,TOY_CURSORS
    if item in THEMES:return (int(item in data['rooms']),sum(room==item for room in data['pet_rooms'].values()))
    owned=total_owned(data,item)
    if item in CATALOG:return owned,sum(item in equipped(data,p) for p in data['wardrobe'])
    used=used_count(data,item)
    # A selected cursor can use an already placed toy without spending another copy.
    if TOY_CURSORS.get(data.get('toy_cursor'))==item:used=max(1,used)
    return owned,used
def placed_here(data,item):return [i for i in data['decorations'][data['pet']] if item_name(i)==item]
def locations(data,item):
    return [f"{data['names'][pet]} / {room}" for (pet,room),items in reservations(data).items() if any(item_name(i)==item for i in items)]
def sync_current(data):
    pet=data['pet'];room=data['pet_rooms'][pet]
    data.setdefault('room_decorations',{}).setdefault(pet,{})[room]=list(data['decorations'][pet])
def new_instance(data,item):
    return item if item not in data['decorations'][data['pet']] else item+'::'+uuid4().hex[:12]
def migrate_inventory(data):
    """Honor all existing room placements once, rather than emptying old rooms."""
    if data.get('decoration_inventory_version')==1:return False
    counts=Counter(item_name(i) for items in reservations(data).values() for i in items)
    for item,used in counts.items():
        if item in data['items'] and used>total_owned(data,item):data['duplicates'][item]=used-1
    data['decoration_inventory_version']=1
    return True
