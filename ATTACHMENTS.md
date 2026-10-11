# Shared accessory attachments

The room, wardrobe preview, and desktop pet use the same attachment renderer.
Accessories are drawn from the 30 existing reusable source pieces (front, side,
and rear views). No accessory animation or outfit/accessory combination artwork
is required. Existing saves and equipment slots still work.

`assets/v5/attachment-rig.json` stores ear, crown, and neck sockets on each pet
pose. Outfits can adjust these small placement records without duplicating art.
Charm placement derives from the collar's ring rather than a separate frame.
Rear-facing pets hide front pendants and bandana fronts. Neckwear is clipped to
the pet silhouette and below the chin line. Source proportions are retained for
bows, hats, bandanas, and charms; collar depth is constrained to the neck.

The initial socket positions were imported from the previous fitted overlays.
The v2 rig corrects 832 left/right walking and running neck sockets to sit
under the chin instead of on the shoulder. Side artwork and charm offsets
mirror together. Sleeping poses hide pendants under the tucked chin.
Rendering cache identities include the renderer version and artwork timestamps,
so updated artwork no longer reuses an earlier generated layer.
They are editable art metadata, not anatomically traced head/ear masks. Strong
head tilts and unusually bulky costumes may still need socket or mask refinement.
The renderer falls back to legacy layers for frames with no rig entry.

Ear bows now work on costumes with built-in headwear. Six costumes still have
headwear painted into the complete pet sprite, so a second hat remains blocked.
To support hat replacement on every outfit, export those costumes with their
headwear as a separate layer and supply a clean underlying head. That art change
cannot be accomplished by attachment coordinates alone.

Run `python test_attachment_rig.py` for geometry/equipment/render checks.
Run `python build_attachment_rig.py` with Pillow only when re-importing old
placement data; this overwrites manual socket adjustments. Pillow is not needed
to play. Generated transparent layers are cached in the system temporary folder;
`LITTLE_COMPANIONS_ATTACHMENT_CACHE` can select a different writable location.
