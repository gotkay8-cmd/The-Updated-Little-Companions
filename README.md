# Little Companions

Desktop companion prototype with a wardrobe fitting room, approved storybook animation artwork, and activity tracking fixes.

In the wardrobe, choose **Try storybook look**, buy any missing items, then **Wear this look**. The matching original outfit + Daisy Ear Bow + Meadow Collar + Acorn Charm combination uses the new complete drawings in the room, desktop pet, and wardrobe. It includes the corrected alternating-paw play loop and Mochi's revised third play frame.

The approved drawings have their accessories painted in. Other wardrobe combinations continue to use the existing customizable artwork; the beret, bandana, and Halloween concept previews are not yet animation assets. Idle uses the neutral play pose, toy uses the play loop, and turning uses the nearest available directional walking pose.

## Run on Windows

Install Python 3.12 or newer with Tcl/Tk, then double-click `Start-Windows.bat`. No extra Python packages are required to play. Use `Debug-Windows.bat` to investigate startup errors.

Keep the complete `assets/` directory alongside the Python files. Progress is stored separately in your Windows user profile.

## Future iterations

- Read `PLAY-GUIDE.md` for features and version history.
- Read `ATTACHMENTS.md` before changing accessory rendering or placement metadata.
- Run `python test_attachment_rig.py` after attachment changes.
- `build_attachment_rig.py` requires Pillow and overwrites manual socket adjustments; run it only when deliberately re-importing placement data.
- Include updated artwork and metadata in each commit so a fresh checkout retains all required assets.

This snapshot includes the application and its artwork. The separate packaged ZIP and workspace preview scripts are outside the application directory.
