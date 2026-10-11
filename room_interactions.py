"""Pointer-driven pet interactions and persistent room arrangement."""
import tkinter as tk
from cozy_ui import CozyMenu
import time
import math
import random
from scene_geometry import room_view,pet_zone,local_pet_point


def layout_value(value, default):
    if not isinstance(value,dict):return dict(default)
    result=dict(default)
    for key,lo,hi in [('x',0,1),('y',0,1),('scale',50,250),('angle',-360,360)]:
        n=value.get(key)
        if type(n) in (int,float) and lo<=n<=hi:result[key]=n
    result['scale']=round(result['scale']/25)*25
    return result


class RoomInteractions:
    def init_interactions(self):
        self.interaction_mode='click';self.pointer=None;self.held=False
        self.selected_decoration=None;self.decoration_drag=None
        self.room_window=None;self.room_canvas=None;self.toy_side=1
        self.previewing_room=None;self.wander=None;self.hover_zone=None;self.spinning=False

    def set_interaction_mode(self,mode):
        if hasattr(self,'debug'):self.debug.event('Interaction mode: '+mode)
        self.interaction_mode=mode;self.held=False;self.decoration_drag=None
        for c in (getattr(self,'canvas',None),self.room_canvas):
            if c and c.winfo_exists():c.configure(cursor={'pet':'none','toy':'none','edit':'fleur'}.get(mode,'arrow'))
        self.notice.set({'click':'Click your pet for a curious reaction.','pet':'Move the hand near your pet’s head to stroke them.','toy':'Move the toy below your pet’s shoulders to play!' ,'edit':'Drag the pet or a decoration. Q / E rotates the selection; scroll resizes. Layout saves automatically.'}[mode])

    def interaction_toolbar(self,parent):
        for title,mode in [('Click','click'),('Pet ✋','pet'),('Play • toy','toy'),('Arrange','edit')]:
            self.button(parent,title,lambda m=mode:self.set_interaction_mode(m))

    def bind_room(self,c):
        c.bind('<ButtonPress-1>',self.room_press)
        c.bind('<Enter>',lambda e:c.focus_set())
        c.bind('<Key-q>',lambda e:self.rotate_selected(-15))
        c.bind('<Key-e>',lambda e:self.rotate_selected(15))
        c.bind('<ButtonRelease-1>',self.room_release)
        c.bind('<Motion>',self.room_motion)
        c.bind('<Leave>',lambda e:self.pointer_leave())
        c.bind('<MouseWheel>',lambda e:self.resize_decoration(25 if e.delta>0 else -25))
        c.bind('<Button-4>',lambda e:self.resize_decoration(25))
        c.bind('<Button-5>',lambda e:self.resize_decoration(-25))
        c.configure(cursor={'pet':'none','toy':'none','edit':'fleur'}.get(self.interaction_mode,'arrow'))

    def pointer_leave(self):
        self.pointer=None
        self.stop_pointer_reaction()

    def decoration_layout(self,item):
        d=self.state.data;p=d['pet'];room=d['pet_rooms'][p]
        layouts=d.setdefault('decoration_layout',{})
        if not isinstance(layouts,dict):layouts={};d['decoration_layout']=layouts
        if not isinstance(layouts.get(p),dict):layouts[p]={}
        if not isinstance(layouts[p].get(room),dict):layouts[p][room]={}
        index=d['decorations'][p].index(item)
        default=dict(x=(.16,.84,.27)[index] if index<3 else .12+(index%6)*.15,y=.94 if index<3 else .90-(index//6%3)*.08,scale=100,angle=0)
        layouts[p][room][item]=layout_value(layouts[p][room].get(item),default)
        return layouts[p][room][item]

    def view(self,c):return room_view(c.winfo_width(),c.winfo_height())

    def decoration_bounds(self,c,item):
        v=self.decoration_layout(item);view=self.view(c);s=90*v['scale']/100*view.scale
        x,y=view.point(v['x'],v['y'])
        angle=math.radians(v.get('angle',0));extent=s*(abs(math.cos(angle))+abs(math.sin(angle)))/2
        return x-extent,y-s/2-extent,x+extent,y-s/2+extent

    def pet_placement(self):
        d=self.state.data;p=d['pet'];room=d['pet_rooms'][p]
        layouts=d.setdefault('pet_layout',{})
        if not isinstance(layouts.get(p),dict):layouts[p]={}
        v=layout_value(layouts[p].get(room),dict(x=.51,y=.96,scale=100,angle=0))
        layouts[p][room]=v
        return v

    def pet_position(self):
        v=self.pet_placement();walk=getattr(self,'wander',None)
        return (walk['x'],walk['y']) if walk else (v['x'],v['y'])

    def pointer_zone(self,c,x,y):
        view=self.view(c);cx,floor=view.point(*self.pet_position());scale=view.scale*self.room_scale/100
        # Rotation is around sprite center; invert it for accurate hover zones.
        center_y=floor-155*scale;angle=math.radians(self.pet_placement()['angle'])
        dx=(x-cx)/scale;dy=(y-center_y)/scale
        lx=dx*math.cos(angle)+dy*math.sin(angle)+180;ly=-dx*math.sin(angle)+dy*math.cos(angle)+155
        walk=getattr(self,'wander',None)
        if walk and self.walking_now():
            direction=walk['direction']
            if direction=='left':lx=360-lx
            if direction in ('left','right'):
                if 218<=lx<=348 and 68<=ly<202:return 'pet'
                if 140<=lx<=340 and 202<=ly<=305:return 'toy'
                return None
        return pet_zone(self.state.data['pet'],lx,ly)

    def pet_hit(self,c,x,y,extra=0):return self.pointer_zone(c,x,y) is not None

    def stop_pointer_reaction(self):
        self.hover_zone=None
        if self.reaction in ('pet','toy'):self.reaction='idle';self.until=0

    def refresh_pointer_reaction(self):
        if getattr(self,'previewing_room',None) or self.interaction_mode=='edit':return
        if self.pointer:
            c,x,y=self.pointer
            if c.winfo_exists() and c.winfo_ismapped():
                zone=self.pointer_zone(c,x,y);self.hover_zone=zone
                c.configure(cursor='none' if zone else 'arrow')
                if zone:
                    self.toy_side=1 if x<self.view(c).point(*self.pet_position())[0] else 3
                    self.start_reaction(zone)
                else:self.stop_pointer_reaction()

    def room_press(self,e):
        if getattr(self,'previewing_room',None):return
        self.held=True;self.pointer=(e.widget,e.x,e.y)
        if self.interaction_mode=='edit':
            self.selected_decoration=None;self.wander=None
            for item in reversed(self.state.data['decorations'][self.state.data['pet']]):
                x0,y0,x1,y1=self.decoration_bounds(e.widget,item)
                if x0<=e.x<=x1 and y0<=e.y<=y1:
                    self.selected_decoration=item;v=self.decoration_layout(item);break
            else:
                if self.pet_hit(e.widget,e.x,e.y):self.selected_decoration='@pet';v=self.pet_placement()
            if self.selected_decoration:
                x,y=self.view(e.widget).point(v['x'],v['y']);self.decoration_drag=(e.x-x,e.y-y)
        else:
            zone=self.pointer_zone(e.widget,e.x,e.y)
            if zone:self.interact(zone)
            self.refresh_pointer_reaction()
        self.render_animals()

    def room_release(self,e):self.held=False;self.decoration_drag=None

    def room_motion(self,e):
        if getattr(self,'previewing_room',None):return
        self.pointer=(e.widget,e.x,e.y)
        if self.interaction_mode=='edit' and self.held and self.decoration_drag and self.selected_decoration:
            v=self.pet_placement() if self.selected_decoration=='@pet' else self.decoration_layout(self.selected_decoration)
            dx,dy=self.decoration_drag;nx,ny=self.view(e.widget).normalized(e.x-dx,e.y-dy)
            v['x']=max(.15,min(.85,nx)) if self.selected_decoration=='@pet' else max(0,min(1,nx))
            v['y']=max(.65,min(.98,ny)) if self.selected_decoration=='@pet' else max(0,min(1,ny))
            self.dirty=True
        else:self.refresh_pointer_reaction()
        self.render_animals()

    def rotate_selected(self,delta):
        if getattr(self,'previewing_room',None) or self.interaction_mode!='edit' or not self.selected_decoration:return
        v=self.pet_placement() if self.selected_decoration=='@pet' else self.decoration_layout(self.selected_decoration)
        v['angle']=(v.get('angle',0)+delta+180)%360-180
        self.dirty=True;self.render_animals()

    def update_wander(self,now):
        if not hasattr(self,'interaction_mode'):return
        if getattr(self,'manual_sleep',False):self.wander=None;return
        if not self.state.data['view_settings'].get('room_roaming',True):self.wander=None;return
        if getattr(self,'spinning',False):
            self.wander=None
            if not getattr(self,'previewing_room',None) and now>=getattr(self,'next_turn',0):self.turn_pet(1);self.next_turn=now+.3
            return
        visible=getattr(self,'panel','Pet Space')=='Pet Space' and (not hasattr(self,'root') or self.root.state()!='iconic')
        if self.interaction_mode=='edit' or getattr(self,'previewing_room',None) or not visible:
            self.wander=None;return
        from walking import new_walk,advance_walk,walking_bounds
        quiet=now-getattr(self,'last_activity',now)
        home=self.pet_placement();home=(home['x'],home['y'])
        if quiet<5 or getattr(self,'hover_zone',None):
            if self.wander:self.wander['at']=now;self.wander['pause']=now+1
            return
        if self.wander is None:
            if quiet>25:return
            self.wander=new_walk(home,now)
        if advance_walk(self.wander,home,walking_bounds(self.room_scale),now,returning=quiet>=25):self.wander=None

    def walking_now(self):
        w=getattr(self,'wander',None)
        return bool(w and w['moving'] and time.monotonic()-getattr(self,'last_activity',0)>=5 and not getattr(self,'hover_zone',None))

    def room_setting(self,key,default):
        d=self.state.data;p=d['pet'];room=d['pet_rooms'][p]
        settings=d.setdefault(key,{})
        if not isinstance(settings.get(p),dict):settings[p]={}
        return settings[p],room,settings[p].get(room,default)

    def pet_facing(self):
        from wardrobe import turn_angles
        TURN_ANGLES=turn_angles(self.state.data,self.state.data['pet'])
        _,_,facing=self.room_setting('pet_facing',0)
        return facing if facing in TURN_ANGLES else 0

    def turn_pet(self,step):
        if getattr(self,'previewing_room',None):return
        from wardrobe import turn_angles
        TURN_ANGLES=turn_angles(self.state.data,self.state.data['pet'])
        settings,room,_=self.room_setting('pet_facing',0)
        settings[room]=TURN_ANGLES[(TURN_ANGLES.index(self.pet_facing())+step)%len(TURN_ANGLES)]
        self.dirty=True

    def toggle_spin(self):
        if not getattr(self,'previewing_room',None):self.spinning=not getattr(self,'spinning',False)

    def current_cushion(self):
        from model import CUSHIONS
        _,_,item=self.room_setting('room_cushions','Default')
        if item in ('Default','None'):return item
        return item if item in CUSHIONS and item in self.state.data['items'] else 'Default'

    def choose_cushion(self,item):
        if getattr(self,'previewing_room',None):return
        from model import CUSHIONS
        if item not in ('Default','None') and (item not in CUSHIONS or item not in self.state.data['items']):return
        from decoration_inventory import free_count,placed_here,locations
        current=self.current_cushion()
        if item not in ('Default','None') and item!=current and not placed_here(self.state.data,item) and free_count(self.state.data,item)<1:
            self.notice.set('This cushion is in '+', '.join(locations(self.state.data,item))+'. Remove it there or buy another copy.');return
        settings,room,_=self.room_setting('room_cushions','Default');settings[room]=item
        if placed_here(self.state.data,item):
            cushion=self.decoration_layout(placed_here(self.state.data,item)[0]);pet=self.pet_placement()
            pet['x']=max(.15,min(.85,cushion['x']));pet['y']=max(.65,min(.98,cushion['y']))
        self.dirty=True;self.render_animals()

    def cushion_menu(self):
        from model import CUSHIONS
        menu=CozyMenu(self.root,tearoff=False)
        current=self.current_cushion()
        from wardrobe import equipped
        if self.state.data['pet']=='Mochi' and equipped(self.state.data,'Mochi'):
            from wardrobe import HALLOWEEN_OUTFITS
            cushion_name='pumpkin' if equipped(self.state.data,'Mochi')[0] in HALLOWEEN_OUTFITS['Mochi'] else 'pink'
            menu.add_command(label=f'This outfit includes a {cushion_name} cushion',state='disabled')
        for item in ['Default','None']+[i for i in CUSHIONS if i in self.state.data['items']]:
            menu.add_command(label=('✓ ' if current==item else '')+item,command=lambda i=item:self.choose_cushion(i))
        if not any(i in self.state.data['items'] for i in CUSHIONS):menu.add_command(label='Buy cushions in Shop',command=lambda:self.show('Shop'))
        self.popup(menu)

    def choose_play_cursor(self,name):
        from model import TOY_CURSORS
        if name not in TOY_CURSORS:return
        item=TOY_CURSORS[name]
        if item is not None and item not in self.state.data['items']:return
        self.state.data['toy_cursor']=name;self.dirty=True;self.set_interaction_mode('toy')

    def set_cursor_scale(self,value):
        if value in (50,75,100,125,150,175,200):self.state.data['cursor_scale']=value;self.dirty=True

    def play_menu(self):
        from model import TOY_CURSORS
        self.set_interaction_mode('toy');menu=CozyMenu(self.root,tearoff=False)
        for name,item in TOY_CURSORS.items():
            if item is None or item in self.state.data['items']:
                menu.add_command(label=('✓ ' if self.state.data['toy_cursor']==name else '')+name,command=lambda n=name:self.choose_play_cursor(n))
        sizing=CozyMenu(menu,tearoff=False)
        for size in (50,75,100,125,150,175,200):sizing.add_command(label=f'{size}%',command=lambda n=size:self.set_cursor_scale(n))
        menu.add_cascade(label='Toy size',menu=sizing);menu.add_separator();menu.add_command(label='Get more toys in Shop',command=lambda:self.show('Shop'))
        self.popup(menu)

    def resize_decoration(self,delta):
        if getattr(self,'previewing_room',None):return
        if self.interaction_mode=='edit' and self.selected_decoration=='@pet':
            self.set_pet_scale(self.room_scale+delta);return
        if self.interaction_mode!='edit' or self.selected_decoration not in self.state.data['decorations'][self.state.data['pet']]:return
        v=self.decoration_layout(self.selected_decoration);v['scale']=max(50,min(250,v['scale']+delta));self.dirty=True
        self.render_animals()

    def fullscreen_room(self):
        if self.room_window and self.room_window.winfo_exists():self.close_room();return
        win=self.room_window=tk.Toplevel(self.root);win.title('Little Companions • Room');win.attributes('-fullscreen',True)
        bar=tk.Frame(win,bg='#fff8eb');bar.pack(fill='x')
        self.button(bar,'← Pet Space',self.close_room);self.interaction_toolbar(bar)
        self.button(bar,'Turn ↶',lambda:self.turn_pet(-1));self.button(bar,'Turn ↷',lambda:self.turn_pet(1))
        self.button(bar,'Spin / stop',self.toggle_spin);self.button(bar,'Cushion',self.cushion_menu);self.button(bar,'Arrange',lambda:self.set_interaction_mode('edit'))
        self.button(bar,'Rotate ↶',lambda:self.rotate_selected(-15));self.button(bar,'Rotate ↷',lambda:self.rotate_selected(15))
        self.button(bar,'Smaller',lambda:self.resize_decoration(-25));self.button(bar,'Larger',lambda:self.resize_decoration(25))
        c=self.room_canvas=tk.Canvas(win,bg='#e9d5b4',highlightthickness=0);c.pack(fill='both',expand=True);self.bind_room(c)
        win.bind('<Escape>',lambda e:self.close_room());win.bind('<F11>',lambda e:self.close_room());win.protocol('WM_DELETE_WINDOW',self.close_room)
        win.focus_set()

    def close_room(self):
        if self.room_window:self.room_window.destroy()
        self.room_window=None;self.room_canvas=None;self.pointer=None;self.held=False
        self.root.deiconify();self.root.lift()
