## v0.47 — Layered accessories and matching collection pages

Ten modular accessories can be purchased with leaves in Shop → Accessories; the five Halloween pieces also appear in Halloween and leave sale on November 7, 2026. Owned pieces remain usable. Equip one head/ear item, one neck item, and one charm per pet alongside an outfit. Charms require Meadow Collar or Midnight Collar; bandanas remove charms. Outfits with built-in headwear block extra headwear. Accessory layers use the currently selected base/outfit frame in rooms and desktop mode, without replacing pet animations. Rear-facing and sleeping charms are hidden where covered; collars/bandanas are concealed by the chin and paws during sleep. Preview uses your selected pet and outfit without changing your save. Collection, Wardrobe, and Rewards adopt the shop’s botanical stationery style. Native Windows rendering still needs visual testing.

## v0.46 — Botanical shop redesign

The shop adopts the supplied accessory-board styling: cream paper cards, scalloped sage and plum borders, stitched peach nameplates, botanical accents, larger item art, serif labels, and plum seasonal stamps. A responsive grid fits up to five cards per row, with the shop section tabs fixed at the left. Halloween remains directly above Duplicates. All existing purchases, previews, inventory actions, prices and expiry rules remain connected. Modular accessories remain concepts, not new inventory items.

## v0.45 — Halloween shop shortcut

Halloween is now a persistent shop sidebar tab directly above Duplicates, linking to a dedicated section with all 21 released Halloween items: 8 outfits, 1 room, 8 decorations, and 4 toys. Existing prices, previews, purchases, and limited-time stickers apply. After November 7, 2026, the section shows an event-ended message; owned items remain available in Collection and Wardrobe. Proposed modular accessories remain preview-only.

## v0.44 — Outfit rarity prices and collection ownership filters

Original outfits: Common, 10 Moonstones. Knit outfits: Rare, 20. Overalls and pajamas: Epic, 40. Halloween outfits: Legendary, 60. Rooms retain their existing prices. Collection now combines All/Owned/Unowned filtering with animal/category and rarity sorting. Owned items remain owned; no repurchase needed. Pajamas remain eligible for gifts at their new Epic tier. Accessories are concept previews only and are not included in this build.

## v0.43 — Pip bat movement and limited Halloween shop

Approved four-frame walk and eight-frame run redraw installed for Pip’s bat outfit, facing both directions. Halloween shop cards carry a Limited Time sticker. Sales and Halloween gift drops end at the start of November 7, 2026, using the computer’s local date; the shop updates while open. Owned items, rooms, outfits, toys, and duplicates remain in your save and usable after the event. Existing rarity tiers and prices are unchanged. This offline prototype uses the device date, not a server-authoritative event clock.

## v0.42 — Approved bat-wing animation redraw

Pip’s bat costume now uses the approved full animation sheet and the corrected petting frame with both front paws down. Reactions, sleep, typing, walking, running, turn views and the shop icon use the redrawn frames. Existing outfit ownership is preserved.

## v0.41 — Pip bat wing correction

Pip’s Little Bat Outfit now has balanced wing attachment at shoulder height across its animation frames. The shop icon and outfit preview use the corrected artwork. Existing ownership and equipped outfits carry over.

## v0.40 — Halloween costume redraws

All eight Halloween costumes now follow the original companion illustration style, with fitted full-character frames for reactions, sleep, typing, four-direction walking, running and turning. Mochi’s Pumpkin Outfit includes a thick pumpkin cushion in its seated reactions. View every animation through Preview in the Shop, Collection or Wardrobe. Existing purchases and outfit selections still work.

## v0.39 — Outfit animation previews

Use Preview on outfit cards in the Shop, Collection, or Wardrobe. All 24 outfits can be previewed before purchase. The showcase cycles through reactions, sleeping, walking in four directions, running both ways, and turning. Choose a motion to loop it, pause or step through frames, and browse previous/next outfits. Previews never spend currency or change your equipped outfit. Close with × or Escape.

# Little Companions v0.38

Extract the entire ZIP into a new folder, then double-click Start-Windows.bat.
Requires Python 3.12 or newer with Tcl/Tk on Windows. No extra Python packages are required to play.
Your existing progress is stored separately in your Windows user profile and carries over automatically.

## Halloween wardrobe
Two new fitted costumes for every pet, 40 Moonstones each in Shop → Clothing:
- Mochi: Little Witch and Pumpkin
- Maple: Cozy Vampire and Harvest Scarecrow
- Clover: Candy Corn and Woodland Fairy
- Pip: Little Bat and Moon Wizard

Purchase in the shop, then equip from Wardrobe. Costumes include reactions, sleeping, turning, four-direction walking and both running directions.

## Pumpkin Parlor and new reactions
- Pumpkin Parlor costs 40 Moonstones and can be previewed in the Rooms scroll.
- Ghost Mouse Plush, Pumpkin Ball Plush, Candy Corn Plush and Bat Plush cost 70 leaves each. Once owned, select them in Play and resize them as usual.
- Eight Halloween decorations cost 40–110 leaves by rarity and can also appear in free gifts. Owned copies can be placed and arranged using Decorate.
- Mochi now sits on a thick pumpkin cushion in her base and Halloween front-facing animations. A separate Pumpkin Cushion is available for room decorating or other pets.
- Base pets and the two Halloween outfits per pet have new petting, playing, sleeping, clicking and typing reactions, with four pet-themed keyboards. Earlier outfits retain their existing fitted artwork.

## Changes
- The player download contains the game and its runtime art, without development source artwork, build tools, automated tests or old preview pages.
- Rooms redraw only when a visible frame, placement, cursor or room setting changes.
- Scaled images use a bounded least-recently-used cache instead of clearing all cached frames at once.
- Unchanged reward and lifetime labels no longer update every animation tick.
- The desktop pet still runs across the taskbar and back, naps for 10 seconds, and repeats.

Use Settings for controls and comfort options. Debug-Windows.bat exports diagnostics if you run into trouble.
