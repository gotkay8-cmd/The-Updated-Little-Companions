"""Shared accessory art fitted to named pet sockets, independent of outfits."""
import json
import struct
import zlib
from functools import lru_cache
from pathlib import Path
from tempfile import gettempdir
from hashlib import sha1
import os

RENDER_VERSION = 2
from png_scaling import read_rgba, chunk

@lru_cache(maxsize=4)
def rig(art_dir):
    path = Path(art_dir)/'attachment-rig.json'
    return json.loads(path.read_text())['frames'] if path.is_file() else {}

def png(width,height,rows):
    return (b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,6,0,0,0))
            +chunk(b'IDAT',zlib.compress(b''.join(b'\0'+bytes(row) for row in rows),1))+chunk(b'IEND',b''))

@lru_cache(maxsize=40)
def part(path):
    """Ignore stray extraction pixels below the main accessory silhouette."""
    w,h,rows=read_rgba(path)
    counts=[sum(row[x*4+3]>32 for x in range(w)) for row in rows]
    occupied=[y for y,n in enumerate(counts) if n>max(counts)*.035]
    top,bottom=min(occupied),max(occupied)+1
    xs=[x for y in range(top,bottom) for x in range(w) if rows[y][x*4+3]>32]
    left,right=min(xs),max(xs)+1
    return right-left,bottom-top,[row[left*4:right*4] for row in rows[top:bottom]]

@lru_cache(maxsize=1024)
def fitted_layer(art_dir,base_path,slug,kind):
    root=Path(art_dir);relative=Path(base_path).relative_to(root).as_posix()
    sockets=rig(str(root)).get(relative)
    if not sockets:return None
    slot={'bow':'ear','hat':'crown','collar':'neck','bandana':'neck','charm':'neck'}[kind]
    socket=sockets.get(slot)
    if not socket:return None
    # Pendant and bandana fronts cannot show through a pet facing away.
    if kind in ('charm','bandana') and not sockets['front_visible']:return None
    source=root/'accessory-parts'/f'{slug}-{sockets["view"]}.png'
    if not source.is_file():return None
    sw,sh,source_rows=part(str(source));w,h,base_rows=read_rgba(base_path)
    cx,cy=socket['x'],socket['y'];width=socket['width']
    name=Path(base_path).stem
    # Sleeping pets tuck their chin onto their chest; the pendant is covered.
    if kind=='charm' and 'sleep' in name:return None
    facing_left='left' in name or name.endswith('turn-270')
    # The shared side drawing points right. Mirror both its artwork and ring
    # offset together when the pet faces left.
    if sockets['view']==1 and facing_left:
        source_rows=[b''.join(row[x*4:x*4+4] for x in range(sw-1,-1,-1)) for row in source_rows]
    if kind=='collar':
        height=max(socket['height'],width*.24)
    elif kind=='bandana':
        width*=.95;height=width*sh/sw;cy+=height*.32
    elif kind=='charm':
        width*=.23;height=width*sh/sw
        # Ring is on the visible right of the collar, shared by every charm.
        cx+=socket['width']*.23*(-1 if facing_left else 1);cy+=socket['height']*.35+height*.40
    else:
        height=width*sh/sw
        if kind=='hat':cy=socket['y']+socket['height']/2-height/2
    width=max(1,round(width));height=max(1,round(height))
    left=round(cx-width/2);top=round(cy-height/2)
    rows=[bytearray(w*4) for _ in range(h)]
    for y in range(max(0,top),min(h,top+height)):
        sy=min(sh-1,int((y-top+.5)*sh/height))
        for x in range(max(0,left),min(w,left+width)):
            sx=min(sw-1,int((x-left+.5)*sw/width));pixel=source_rows[sy][sx*4:sx*4+4]
            if kind in ('collar','bandana'):
                # Neckwear follows the body silhouette; its rear edge sits under
                # the chin instead of painting across the face and hanging ears.
                if base_rows[y][x*4+3]<32:continue
                if y<socket['y']-socket['height']*.20:continue
            rows[y][x*4:x*4+4]=pixel
    cache=Path(os.environ.get('LITTLE_COMPANIONS_ATTACHMENT_CACHE',gettempdir()))/'little-companions-attachments-v1'
    cache.mkdir(parents=True,exist_ok=True)
    identity=sha1((str(RENDER_VERSION)+str(root.resolve())+relative+slug+
                   json.dumps(sockets,sort_keys=True)+
                   str(source.stat().st_mtime_ns)+str(Path(base_path).stat().st_mtime_ns)).encode()).hexdigest()
    output=cache/(identity+'.png')
    if not output.is_file():
        temporary=output.with_suffix('.tmp');temporary.write_bytes(png(w,h,rows));temporary.replace(output)
    return output

def attachment_paths(art_dir,pet,base_path,items,definitions):
    relative=Path(base_path).relative_to(Path(art_dir)).as_posix()
    if relative not in rig(str(Path(art_dir))):return None
    return [path for item in items
            if (path:=fitted_layer(str(Path(art_dir)),str(base_path),item.lower().replace(' ','-'),definitions[item]['kind']))]
