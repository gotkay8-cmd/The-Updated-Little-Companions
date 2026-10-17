"""Bounded image reuse and inexpensive room redraw invalidation."""
from collections import OrderedDict
import time

class ImageCache(OrderedDict):
    """Evict least recently used frames, never flush the entire animation set."""
    def __init__(self,max_pixels=24000000,max_entries=320):
        super().__init__();self.max_pixels=max_pixels;self.max_entries=max_entries;self.pixels=0
    def __getitem__(self,key):
        value=super().__getitem__(key);self.move_to_end(key);return value
    def __setitem__(self,key,value):
        if key in self:self.pixels-=self[key].width()*self[key].height()
        super().__setitem__(key,value);self.move_to_end(key);self.pixels+=value.width()*value.height()
        while len(self)>1 and (len(self)>self.max_entries or self.pixels>self.max_pixels):
            _,old=self.popitem(last=False);self.pixels-=old.width()*old.height()
    def clear(self):
        super().clear();self.pixels=0

def scene_key(app,canvas):
    d=app.state.data;p=d['pet'];now=time.monotonic()
    room=getattr(app,'previewing_room',None) or d['pet_rooms'][p]
    geometry=(canvas.winfo_width(),canvas.winfo_height(),room)
    if getattr(app,'previewing_room',None):return geometry+('preview',)
    motion,index=app.sprite_state(p)
    walk=getattr(app,'wander',None)
    from layered_animation import walking_timing
    movement=None
    if walk and app.walking_now():
        count,interval=walking_timing(walk['direction'])
        movement=(walk['direction'],int((now-walk['started'])/interval)%count)
    # Snapshot mutable placements rather than retaining references to save data.
    decor=tuple((str(item),tuple(sorted(app.decoration_layout(item).items()))) for item in d['decorations'][p])
    remotes=tuple((q['id'],q['pet'],q['name'],q['reaction'],app.sprite_state(q['pet'],q['reaction'])) for q in app.remote if q['id']!=app.player_id)
    sleeping=motion=='sleep' or any(q[3]=='sleep' for q in remotes)
    from wardrobe import equipped
    return geometry+(p,motion,index,app.room_scale,app.pet_position(),tuple(sorted(app.pet_placement().items())),app.pet_facing(),app.current_cushion(),tuple(equipped(d,p)),decor,remotes,movement,bool(walk),app.interaction_mode,app.selected_decoration,getattr(app,'hover_zone',None),getattr(app,'pointer',None),getattr(app,'spinning',False),d.get('toy_cursor'),d.get('cursor_scale'),int(now*30) if sleeping else 0)

def configure_changed(widget,**options):
    """Avoid sending unchanged counters back through Tcl every game tick."""
    previous=getattr(widget,'_cozy_last_options',None)
    if previous!=options:
        widget.configure(**options);widget._cozy_last_options=options
