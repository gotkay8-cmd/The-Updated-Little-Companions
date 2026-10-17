# Little Companions

Desktop companion prototype with a wardrobe fitting room, layered pet animations, and activity tracking.

Version 0.60 installs extracted and aligned 2D clothing for all 24 outfits across nine motion groups, including mirrored side walks and runs. Clothing stays removable; the approved base pets, accessories, saved purchases, and walk-away clothing visibility are unchanged.

Version 0.57 hides clothing while any pet walks away (Walk up), including wardrobe previews. Accessories remain visible. Outfits stay equipped for other animations, and purchases are preserved.

This download includes the new typing, petting, playing, clicking, sleeping, walking, and running base animations for all four pets. Clothing and accessories use separate fitted layers. Use the wardrobe arrows to preview items, buy them, and choose **Wear this look**.

Stationary animations share a ground anchor. The seated idle uses approved neutral and soft-blink poses. Cursor play and petting follow the cursor's screen side. Retired animation and wardrobe files have been removed from this package; turns use the approved walking directions.

Version 0.53 ties typing frames to keystrokes and clicking playback to the measured click pace. Playing and clicking collars now use per-frame neck anchors, with the face and raised paws in front.

Version 0.54 includes all 24 outfits across every installed animation, including sitting, reactions, sleeping, walking, and running. Running charms remain temporarily hidden while purchases and selections stay saved. See `ANIMATION-INSTALL-STATUS.md` and `REMAINING-ART.json` for coverage and remaining work.

Clothing remains in separate removable layers, with arms in front and stabilized fabric placement.

## Run on Windows

Extract the ZIP first. Install Python 3.12 or newer with Tcl/Tk and the Windows Python launcher, then open the extracted `Little-Companions` folder and double-click `Start-Windows.bat`. No extra Python packages are required to play. This is a Python game package, not a standalone executable. Use `Debug-Windows.bat` to investigate startup errors.

Keep the complete `assets/` directory alongside the Python files. Progress is stored separately in your Windows user profile.

## Future iterations

- Read `PLAY-GUIDE.md` for features and version history.
- Read the manifests under `assets/v5/layered-motions` and `assets/v5/layered-walk` before changing fitted artwork.
- Run `python -m unittest discover` after changes. Runtime tests use a temporary save.
- Include updated artwork and metadata in each commit so a fresh checkout retains all required assets.

This snapshot includes the application and its artwork. The separate packaged ZIP and workspace preview scripts are outside the application directory.

Version 0.58 installs Clover's approved Garden outfit redraw for all 16 walking-toward frames as separate clothing layers. Original base art and purchases are preserved. Walk-up clothing remains hidden. Other outfit designs retain their existing installed artwork.
