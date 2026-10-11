"""Presentation names are separate from stable inventory and sprite IDs."""
import re
def display_text(data,text):
    if not isinstance(text,str):return text
    names=data.get('names',{})
    return re.sub(r'\b(Mochi|Maple|Clover|Pip)\b',lambda m:names.get(m[0],m[0]),text)

def rarity_sorted(items,order):
    from model import ITEM_RARITY
    ranks={'Common':0,'Uncommon':1,'Rare':2,'Epic':3,'Legendary':4}
    return sorted(items,key=lambda item:((-1 if order=='Rarest first' else 1)*ranks[ITEM_RARITY[item]],item))
