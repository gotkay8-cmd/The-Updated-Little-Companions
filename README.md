# Little Companions

Desktop companion prototype with a wardrobe fitting room and v0.49 activity tracking fixes.

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
