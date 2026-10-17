"""A fitting-room draft: browsing never changes ownership or worn equipment."""
from wardrobe import CATALOG, SLOTS, available, outfit_sprite
from accessory_layers import COLLARS, head_conflict, layer_paths
from pathlib import Path


class WardrobeDraft:
    def __init__(self, data, pet):
        self.pet = pet
        self.slots = dict(data.get('wardrobe', {}).get(pet, {}))
        self.normalize()

    def normalize(self):
        self.slots = {s: i for s, i in self.slots.items()
                      if s in SLOTS and available(i, self.pet) and CATALOG[i]['slot'] == s}
        if self.slots.get('neck') not in COLLARS:
            self.slots.pop('charm', None)
        head = self.slots.get('head')
        if head and head_conflict(self.slots, head):
            self.slots.pop('head')

    def options(self, slot, data):
        from model import shop_available
        return [None] + [i for i, info in CATALOG.items()
                        if info['slot'] == slot and available(i, self.pet)
                        and (i in data.get('items', []) or shop_available(i))
                        and not (slot == 'head' and head_conflict(self.slots, i))
                        and not (slot == 'charm' and self.slots.get('neck') not in COLLARS)]

    def cycle(self, slot, step, data):
        choices = self.options(slot, data)
        current = self.slots.get(slot)
        index = choices.index(current) if current in choices else 0
        item = choices[(index + step) % len(choices)]
        if item is None:
            self.slots.pop(slot, None)
        else:
            self.slots[slot] = item
        self.normalize()

    def missing(self, data):
        return [i for i in self.slots.values() if i not in data.get('items', [])]

    def apply(self, data):
        self.normalize()
        if self.missing(data):
            return False
        data.setdefault('wardrobe', {})[self.pet] = dict(self.slots)
        return True

    def paths(self, art_dir, motion='Idle', frame=0):
        from outfit_preview import REACTIONS
        data = {'items': list(self.slots.values()), 'wardrobe': {self.pet: dict(self.slots)}}
        kwargs = {}
        name = REACTIONS.get(motion, 'idle') + '-' + str(frame % 4)
        if motion.startswith('Walk '):
            kwargs['walking'] = motion.split()[1]
            name = 'walk-' + kwargs['walking'] + '-' + str(frame % 4)
        elif motion.startswith('Run '):
            kwargs['running'] = motion.split()[1]
            name = 'run-' + kwargs['running'] + '-' + str(frame % 8)
        elif motion == 'Turn around':
            from wardrobe import turn_angles
            angles = turn_angles(data, self.pet)
            angle = angles[frame % len(angles)]
            kwargs['facing'] = angle
            name = 'turn-' + str(angle) if angle else 'idle-0'
        base = outfit_sprite(art_dir, data, self.pet, REACTIONS.get(motion, 'idle'), frame, **kwargs)
        if base is None:
            filename = (self.pet.lower() + '-' + name + '.png' if name.startswith(('walk', 'run', 'turn'))
                        else self.pet.lower() + '_' + name.replace('-', '_') + '.png')
            base = Path(art_dir) / filename
        return [base] + layer_paths(art_dir, data, self.pet, base)
