"""Approved complete drawings for the matching floral wardrobe combination."""
from pathlib import Path

ACCESSORIES = {'head': 'Daisy Ear Bow', 'neck': 'Meadow Collar', 'charm': 'Acorn Charm'}

def approved_slots(pet):
    from wardrobe import OUTFITS
    return dict(ACCESSORIES, outfit=OUTFITS[pet])

def approved_sprite(art_dir, data, pet, name):
    expected = approved_slots(pet)
    slots = data.get('wardrobe', {}).get(pet, {})
    owned = data.get('items', [])
    if not all(slots.get(slot) == item and item in owned for slot, item in expected.items()):
        return None
    path = Path(art_dir) / 'approved' / pet.lower() / (name + '.png')
    return path if path.is_file() else None

def is_approved_frame(art_dir, base_path):
    try:
        return Path(base_path).resolve().is_relative_to((Path(art_dir) / 'approved').resolve())
    except (ValueError, OSError):
        return False
