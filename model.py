"""Persistent, local-only progression. No keyboard text is ever saved."""
import json
import random
from decoration_inventory import item_name,total_owned,free_count,placed_here,locations,sync_current,new_instance,migrate_inventory
from wardrobe import CATALOG,SLOTS,available,RETIRED,migrate_clothing
from datetime import date,datetime,timezone
from functools import lru_cache
from pathlib import Path

PETS = {
    'Mochi': ('Curious • Creative', '#f5dfbd', 'Cozy Nook', 'Nook decoration'),
    'Maple': ('Affectionate • Cheerful', '#dba057', 'Toy Room', 'Soft toy'),
    'Clover': ('Gentle • Quietly curious', '#a7b499', 'Pocket Garden', 'Flower pot'),
    'Pip': ('Playful • Mischievous', '#bf6d43', 'Woodland', 'Tiny treasure'),
}
THEMES = ['Cozy Nook', 'Toy Room', 'Pocket Garden', 'Woodland', 'Seaside', 'Starlight Attic', 'Blossom Conservatory','Pumpkin Parlor']
ROOM_PRICES={'Seaside':30,'Starlight Attic':40,'Blossom Conservatory':40,'Pumpkin Parlor':40}
SIGNATURE_ITEMS = {
    'Mochi': ['Yarn Basket', 'Fish Teaser', 'Crescent Cushion'],
    'Maple': ['Bone Basket', 'Tennis Ball Jar', 'Paw Blanket'],
    'Clover': ['Carrot Planter', 'Daisy Cushion', 'Watering Can'],
    'Pip': ['Treasure Chest', 'Acorn Lantern', 'Mushroom Stool'],
}
HALLOWEEN_TOYS={'Mochi':'Ghost Mouse Plush','Maple':'Pumpkin Ball Plush','Clover':'Candy Corn Plush','Pip':'Bat Plush'}
HALLOWEEN_DECOR=['Pumpkin Cushion','Ghost Lantern','Cozy Cauldron','Pumpkin Garland','Spooky Mushroom Lamp','Autumn Spellbooks','Bat Mobile','Trick-or-Treat Basket']
# Keep catalog entries permanently: old saves and owned equipment still need them.
HALLOWEEN_END=date(2026,11,7)
HALLOWEEN_ITEMS=frozenset(HALLOWEEN_DECOR+list(HALLOWEEN_TOYS.values())+['Pumpkin Parlor']+[name for name,info in CATALOG.items() if info.get('season')=='Halloween'])
def halloween_active(today=None):
    return (date.today() if today is None else today)<HALLOWEEN_END

def shop_available(item,today=None):
    return item not in HALLOWEEN_ITEMS or halloween_active(today)

for pet,toy in HALLOWEEN_TOYS.items():SIGNATURE_ITEMS[pet].append(toy)
UNIVERSAL_TOYS=['Star Plush','Heart Plush','Ribbon Wand','Butterfly Plush','Cloud Plush','Jingle Ring']
SHARED_DECOR=['Braided Rug','Reading Basket','Mushroom Lamp','Daisy Vase','Cozy Tent','Star Mobile','Toy Chest','Little Bookcase']+HALLOWEEN_DECOR
ACCESSORIES = list(CATALOG)
DECORATIONS = ['Cushion', 'Plant', 'Toy', 'Lamp'] + [i for group in SIGNATURE_ITEMS.values() for i in group] + SHARED_DECOR + UNIVERSAL_TOYS
ITEMS = DECORATIONS + ACCESSORIES
TOY_CURSORS={'Favorite toy':None,'Duck plush':'Toy',**{name:name for name in UNIVERSAL_TOYS+list(HALLOWEEN_TOYS.values())}}
DEFAULT_TOYS={'Mochi':'mochi','Maple':'maple','Clover':'carrot-plush','Pip':'pip'}
CUSHIONS=('Cushion','Crescent Cushion','Daisy Cushion','Paw Blanket','Pumpkin Cushion')
TURN_ANGLES=(0,90,135,180,225,270)
RARITY_PRICES={'Common':20,'Uncommon':40,'Rare':70,'Epic':110}
SELL_VALUES={'Common':5,'Uncommon':20,'Rare':50,'Epic':100,'Legendary':100}
def sale_value(item):return SELL_VALUES[ITEM_RARITY.get(item,'Common')]
RARITY_ODDS={'Common':59,'Uncommon':25,'Rare':12,'Epic':3,'Legendary':1}
RARITY_COLORS={'Common':'#718763','Uncommon':'#528d92','Rare':'#8872ad','Epic':'#b78643','Legendary':'#bd7730'}
ITEM_RARITY={item:'Common' for item in ITEMS+THEMES}
for item in ['Lamp','Yarn Basket','Bone Basket','Carrot Planter','Watering Can','Braided Rug','Reading Basket','Daisy Vase','Star Plush','Heart Plush','Cloud Plush']:
    ITEM_RARITY[item]='Uncommon'
for item in ['Fish Teaser','Tennis Ball Jar','Paw Blanket','Daisy Cushion','Mushroom Stool','Mushroom Lamp','Toy Chest','Butterfly Plush','Ribbon Wand','Seaside']:
    ITEM_RARITY[item]='Rare'
for item in ['Crescent Cushion','Acorn Lantern','Treasure Chest','Cozy Tent','Star Mobile','Little Bookcase','Jingle Ring','Starlight Attic','Blossom Conservatory']+ACCESSORIES:
    ITEM_RARITY[item]='Epic'
for item in HALLOWEEN_TOYS.values():ITEM_RARITY[item]='Rare'
for item in ['Pumpkin Cushion','Autumn Spellbooks','Trick-or-Treat Basket']:ITEM_RARITY[item]='Uncommon'
for item in ['Ghost Lantern','Pumpkin Garland','Spooky Mushroom Lamp']:ITEM_RARITY[item]='Rare'
for item in ['Cozy Cauldron','Bat Mobile','Pumpkin Parlor']:ITEM_RARITY[item]='Epic'
ITEM_RARITY.update({item:info['rarity'] for item,info in CATALOG.items()})
PREMIUM_PRICES={**ROOM_PRICES,**{item:CATALOG[item]['price'] for item in ACCESSORIES if CATALOG[item]['slot']=='outfit'}}
CURRENCY_NAME='Moonstones'
def price_for(item):
    return ('moonstones',PREMIUM_PRICES[item]) if item in PREMIUM_PRICES else ('coins',RARITY_PRICES[ITEM_RARITY.get(item,'Common')])
def price_label(item):
    currency,cost=price_for(item)
    return f'{cost} '+('Moonstones' if currency=='moonstones' else 'leaves')
MOONSTONE_PRIZE='40 Moonstones'
LEGENDARY_ITEMS=['Starlight Attic','Blossom Conservatory',MOONSTONE_PRIZE]
GIFT_OUTFITS=['Mochi Lavender Pajamas Outfit','Maple Sky Pajamas Outfit','Clover Chamomile Pajamas Outfit','Pip Acorn Pajamas Outfit']
for item in LEGENDARY_ITEMS:ITEM_RARITY[item]='Legendary'
FREE_GIFT_POOL=DECORATIONS+LEGENDARY_ITEMS+GIFT_OUTFITS
# Integer tickets preserve exact tier odds and equal odds within each tier.
from math import lcm
_tier_counts={tier:sum(ITEM_RARITY[i]==tier for i in FREE_GIFT_POOL) for tier in RARITY_ODDS}
_ticket_unit=lcm(*_tier_counts.values())
GIFT_TICKETS=[item for item in FREE_GIFT_POOL for _ in range(RARITY_ODDS[ITEM_RARITY[item]]*_ticket_unit//_tier_counts[ITEM_RARITY[item]])]
@lru_cache(maxsize=2)
def seasonal_gift_tickets(active):
    if active:return GIFT_TICKETS
    pool=[i for i in FREE_GIFT_POOL if i not in HALLOWEEN_ITEMS]
    counts={tier:sum(ITEM_RARITY[i]==tier for i in pool) for tier in RARITY_ODDS}
    unit=lcm(*counts.values())
    return [i for i in pool for _ in range(RARITY_ODDS[ITEM_RARITY[i]]*unit//counts[ITEM_RARITY[i]])]

GIFT_THRESHOLD = 250
LEAF_BONUS_THRESHOLD=1000
LEAF_BONUS_AMOUNT=200

class GameState:
    def __init__(self, path):
        self.path = Path(path)
        self.data = dict(version=1, pet='Mochi', names={p:p for p in PETS},
                         points=0, coins=0, moonstones=0, gifts=0, total=0, clicks=0, keystrokes=0, leaf_bonus_progress=0, leaf_bonus_awards=0, items=[],
                         rooms=THEMES[:4], pet_rooms={p:v[2] for p,v in PETS.items()},
                         decorations={p:[] for p in PETS}, accessory={p:'' for p in PETS},wardrobe={p:{} for p in PETS},
                         decoration_inventory_version=1, decoration_layout={}, room_decorations={}, pet_layout={}, toy_cursor='Favorite toy',cursor_scale=100,room_cushions={},pet_facing={}, duplicates={},reward_history=[],
                         view_settings=dict(room_scale=100,desktop_scale=100,background_activity=True,reduced_effects=False,room_roaming=True,auto_desktop=True,low_power=False,taskbar_running=True))
        self.warning = '';self.migration_notice = ''
        if self.path.exists():
            try:
                loaded = json.loads(self.path.read_text(encoding='utf-8'))
                if not isinstance(loaded, dict) or loaded.get('version') != 1:
                    raise ValueError('Unsupported save')
                if type(loaded.get('moonstones',0)) is not int or loaded.get('moonstones',0)<0:loaded['moonstones']=0
                for k in ('clicks','keystrokes'):
                    loaded[k]=loaded.get(k,0) if type(loaded.get(k,0)) is int and loaded.get(k,0)>=0 else 0
                progress=loaded.get('leaf_bonus_progress',(loaded['clicks']+loaded['keystrokes'])%LEAF_BONUS_THRESHOLD)
                loaded['leaf_bonus_progress']=progress if type(progress) is int and 0<=progress<LEAF_BONUS_THRESHOLD else 0
                awards=loaded.get('leaf_bonus_awards',0)
                loaded['leaf_bonus_awards']=awards if type(awards) is int and awards>=0 else 0
                for k in ('points','coins','gifts','total'):
                    if type(loaded.get(k)) is not int or loaded[k] < 0:
                        raise ValueError('Invalid progress')
                if loaded.get('pet') not in PETS:
                    raise ValueError('Invalid pet')
                for k in ('names','pet_rooms','decorations','accessory'):
                    if not isinstance(loaded.get(k),dict) or not all(p in loaded[k] for p in PETS):
                        raise ValueError('Invalid collection')
                if any(not isinstance(loaded['names'][p],str) or len(loaded['names'][p])>24 for p in PETS):
                    raise ValueError('Invalid names')
                if not isinstance(loaded.get('rooms'),list) or any(r not in THEMES for r in loaded['rooms']):
                    raise ValueError('Invalid rooms')
                self.migration_notice=migrate_clothing(loaded)
                if not isinstance(loaded.get('items'),list) or any(i not in ITEMS for i in loaded['items']):
                    raise ValueError('Invalid items')
                for p in PETS:
                    if loaded['pet_rooms'][p] not in loaded['rooms']:
                        raise ValueError('Invalid room assignment')
                    if not isinstance(loaded['decorations'][p],list) or any(item_name(i) not in loaded['items'] or item_name(i) not in DECORATIONS for i in loaded['decorations'][p]):
                        raise ValueError('Invalid decorations')
                    if loaded['accessory'][p] and (loaded['accessory'][p] not in loaded['items'] or loaded['accessory'][p] not in ACCESSORIES):
                        raise ValueError('Invalid accessory')
                raw=loaded.get('wardrobe',{})
                if not isinstance(raw,dict):raw={}
                loaded['wardrobe']={}
                for pet in PETS:
                    slots=raw.get(pet,{})
                    if not isinstance(slots,dict):slots={}
                    cleaned={slot:item for slot,item in slots.items() if slot in SLOTS and item in loaded['items'] and available(item,pet) and CATALOG[item]['slot']==slot}
                    if 'accessory' not in cleaned and loaded['accessory'][pet]:cleaned['accessory']=loaded['accessory'][pet]
                    loaded['wardrobe'][pet]=cleaned
                prefs=loaded.get('view_settings',{})
                if not isinstance(prefs,dict):prefs={}
                loaded['view_settings']={
                    'room_scale':prefs.get('room_scale') if prefs.get('room_scale') in (50,75,100,125,150) else 100,
                    'desktop_scale':prefs.get('desktop_scale') if prefs.get('desktop_scale') in (50,75,100,125,150) else 100,
                    'background_activity':prefs.get('background_activity') if type(prefs.get('background_activity')) is bool else True,
                }
                for key,default in [('reduced_effects',False),('room_roaming',True),('auto_desktop',True),('low_power',False),('taskbar_running',True)]:
                    loaded['view_settings'][key]=prefs.get(key,default) if type(prefs.get(key,default)) is bool else default
                duplicates=loaded.get('duplicates',{})
                loaded['duplicates']={k:v for k,v in duplicates.items() if k in ITEMS+THEMES and type(v) is int and v>0 and k in loaded['items']+loaded['rooms']} if isinstance(duplicates,dict) else {}
                history=loaded.get('reward_history',[])
                loaded['reward_history']=[e for e in history if isinstance(e,dict) and e.get('item') in ITEMS+THEMES+list(RETIRED)+[MOONSTONE_PRIZE] and e.get('action') in ('gift','sale')] if isinstance(history,list) else []
                for key in ('room_decorations','pet_layout','room_cushions','pet_facing'):
                    if not isinstance(loaded.get(key,{}),dict):loaded[key]={}
                layouts=loaded.get('room_decorations',{})
                loaded['room_decorations']={p:{r:list(dict.fromkeys(i for i in items if item_name(i) in loaded['items'] and item_name(i) in DECORATIONS)) for r,items in rooms.items() if r in THEMES and isinstance(items,list)} for p,rooms in layouts.items() if p in PETS and isinstance(rooms,dict)}
                if loaded.get('toy_cursor','Favorite toy') not in TOY_CURSORS:loaded['toy_cursor']='Favorite toy'
                if TOY_CURSORS.get(loaded.get('toy_cursor')) not in loaded['items']:loaded['toy_cursor']='Favorite toy'
                if loaded.get('cursor_scale',100) not in (50,75,100,125,150,175,200):loaded['cursor_scale']=100
                if migrate_inventory(loaded):
                    self.migration_notice=(self.migration_notice+' Existing decorations now reserve individual copies; your room layouts have been kept.').strip()
                self.data.update({k:loaded[k] for k in self.data if k in loaded})
            except (OSError,ValueError,KeyError,TypeError):
                self.warning = 'Your save could not be loaded. The original is kept as save.recovery.json.'
                import shutil
                shutil.copy2(self.path, self.path.with_name('save.recovery.json'))

    def place_decoration(self,item):
        d=self.data
        if item not in DECORATIONS or item not in d['items']:return 'Own this decoration before placing it.'
        pet=d['pet'];room=d['pet_rooms'][pet]
        seat=d.get('room_cushions',{}).get(pet,{}).get(room)
        # A cushion already serving as this room's seat can acquire a layout
        # without reserving a second copy.
        reserved_seat=seat==item and not placed_here(d,item)
        if free_count(d,item)<1 and not reserved_seat:
            return 'All copies are placed in '+', '.join(locations(d,item))+'. Remove one there or buy another copy.'
        d['decorations'][pet].append(new_instance(d,item));sync_current(d)
        return 'Placed '+item+'.'

    def remove_decoration(self,item):
        d=self.data;pet=d['pet'];room=d['pet_rooms'][pet]
        matches=placed_here(d,item_name(item))
        if not matches:
            if d.get('room_cushions',{}).get(pet,{}).get(room)==item_name(item):
                d['room_cushions'][pet][room]='None'
                return 'Removed '+item_name(item)+'. That copy is available again.'
            return 'This decoration is not placed here.'
        target=item if '::' in item and item in matches else matches[-1]
        d['decorations'][pet].remove(target)
        if not placed_here(d,item_name(item)) and d.get('room_cushions',{}).get(pet,{}).get(room)==item_name(item):
            d['room_cushions'][pet][room]='None'
        sync_current(d)
        return 'Removed '+item_name(item)+'. That copy is available again.'

    def switch_room(self,room):
        if room not in self.data['rooms']:return False
        d=self.data;p=d['pet'];old=d['pet_rooms'][p]
        rooms=d.setdefault('room_decorations',{}).setdefault(p,{})
        rooms[old]=list(d['decorations'][p])
        d['decorations'][p]=list(rooms.get(room,[]))
        d['pet_rooms'][p]=room
        return True

    def save(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        temporary = self.path.with_suffix('.tmp')
        temporary.write_text(json.dumps(self.data,indent=2),encoding='utf-8')
        temporary.replace(self.path)

    def activity(self, count=1, kind=None):
        count = min(10,max(0,int(count)))
        bonus=0
        if kind in ('clicks','keystrokes'):
            self.data[kind]+=count
            awards,self.data['leaf_bonus_progress']=divmod(self.data['leaf_bonus_progress']+count,LEAF_BONUS_THRESHOLD)
            bonus=awards*LEAF_BONUS_AMOUNT;self.data['coins']+=bonus;self.data['leaf_bonus_awards']+=awards
        self.data['total'] += count
        self.data['points'] += count
        while self.data['points'] >= GIFT_THRESHOLD:
            self.data['points'] -= GIFT_THRESHOLD
            self.data['gifts'] += 1
        return bonus

    def open_gift(self, rng=random):
        if self.data['gifts'] < 1:
            return 'Keep typing or playing to earn a gift.'
        # Only the selected Legendary premium items enter the free gift pool.
        item=rng.choice(seasonal_gift_tickets(halloween_active()))
        if item not in FREE_GIFT_POOL or not shop_available(item):raise ValueError('Reward is not in the active gift pool')
        self.data['gifts'] -= 1
        self.data['coins'] += 15
        if item==MOONSTONE_PRIZE:
            self.data['moonstones']+=40;self.last_reward=dict(item=item,rarity='Legendary',duplicate=False,moonstones=40)
            self.data['reward_history'].append(dict(at=datetime.now(timezone.utc).isoformat(timespec='seconds'),action='gift',item=item,rarity='Legendary',duplicate=False,leaves=15,moonstones=40))
            return 'Legendary prize: 40 Moonstones and 15 leaves!'
        collection = 'rooms' if item in THEMES else 'items'
        self.last_reward=dict(item=item,rarity=ITEM_RARITY[item],duplicate=item in self.data[collection])
        self.data['reward_history'].append(dict(at=datetime.now(timezone.utc).isoformat(timespec='seconds'),action='gift',item=item,rarity=ITEM_RARITY[item],duplicate=self.last_reward['duplicate'],leaves=15))
        if item in self.data[collection]:
            self.data['duplicates'][item]=self.data['duplicates'].get(item,0)+1
            return f'Duplicate {item} kept in inventory. +15 gift leaves!'
        self.data[collection].append(item)
        return f'Unlocked {ITEM_RARITY[item]} {item} and earned 15 leaves!'

    def open_gifts(self,count,rng=random):
        if type(count) is not int or count<1 or count>self.data['gifts']:return []
        results=[]
        for _ in range(count):
            self.open_gift(rng);results.append(dict(self.last_reward))
        return results

    def exchange_currency(self,direction,units):
        if type(units) is not int or units<1:return 'Enter a positive whole number of Moonstones.'
        if direction not in ('to_leaves','to_moonstones'):return 'Choose an exchange direction.'
        source,target,cost,gain=('moonstones','coins',units,units*1000) if direction=='to_leaves' else ('coins','moonstones',units*1000,units)
        if self.data[source]<cost:return 'Not enough currency for that exchange.'
        self.data[source]-=cost;self.data[target]+=gain
        return f'Exchanged {cost:,} '+('Moonstones for ' if source=='moonstones' else 'leaves for ')+f'{gain:,} '+('leaves.' if target=='coins' else 'Moonstones.')

    def rename_pet(self,pet,name):
        if pet not in PETS or not isinstance(name,str):return 'Choose a valid pet and name.'
        name=name.strip()
        if not name or len(name)>24 or any(ord(c)<32 for c in name):return 'Use a name of 1–24 characters.'
        if name==self.data['names'][pet]:return 'That is already their name. No leaves spent.'
        if self.data['coins']<30:return 'You need 30 leaves to rename your pet.'
        self.data['coins']-=30;self.data['names'][pet]=name
        return f'Your companion is now {name}! Spent 30 leaves.'

    def buy(self, item):
        collection = 'rooms' if item in THEMES else 'items'
        if item not in ITEMS + list(ROOM_PRICES):
            return 'Unknown item.'
        if not shop_available(item):return 'This limited-time Halloween item left the shop on November 7, 2026. Owned copies are yours to keep.'
        currency,cost=price_for(item)
        if item in self.data[collection] and item not in DECORATIONS:
            return 'Already unlocked.'
        if self.data[currency] < cost:
            return f'You need {cost} Moonstones. Use currency exchange or find Legendary gifts.' if currency=='moonstones' else f'You need {cost} leaves. Earn leaves from free gifts.'
        self.data[currency] -= cost
        if item in self.data[collection]:
            self.data['duplicates'][item]=self.data['duplicates'].get(item,0)+1
            return f'Bought another {item}. {total_owned(self.data,item)} copies owned.'
        self.data[collection].append(item)
        return f'Unlocked {item}!'

    def sell_duplicate(self,item):
        count=self.data['duplicates'].get(item,0)
        if count<1:return 'No spare copy to sell. Your original is kept.'
        if item in DECORATIONS and free_count(self.data,item)<1:return 'Every copy is placed. Remove one from a room before selling it.'
        if count==1:self.data['duplicates'].pop(item)
        else:self.data['duplicates'][item]=count-1
        value=sale_value(item);self.data['coins']+=value
        self.data['reward_history'].append(dict(at=datetime.now(timezone.utc).isoformat(timespec='seconds'),action='sale',item=item,leaves=value))
        return f'Sold one duplicate {item} for {value} leaves. Original kept.'
