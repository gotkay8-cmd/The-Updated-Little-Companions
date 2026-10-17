"""A coordinated equipment preset; all rendering uses separate approved layers."""

ACCESSORIES = {'head': 'Daisy Ear Bow', 'neck': 'Meadow Collar', 'charm': 'Acorn Charm'}

def approved_slots(pet):
    from wardrobe import OUTFITS
    return dict(ACCESSORIES, outfit=OUTFITS[pet])

