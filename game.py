"""Little Companions: Windows-first playable development prototype."""
import ctypes
import math
import os
from pathlib import Path
import queue
import secrets
import sys
import threading
import time
import tkinter as tk
from cozy_ui import CozyMenu
from wardrobe import CATALOG,available,equipped
from tkinter import ttk
from cozy_dialogs import messagebox,simpledialog
from model import GameState, PETS, THEMES, ITEMS, GIFT_THRESHOLD, ACCESSORIES
from network import RoomServer, exchange
from input_events import BackgroundInput
from cozy_ui import CozyButton,install_fonts
from reference_ui import ReferenceUI
from room_interactions import RoomInteractions
from desktop_overlay import DesktopOverlay, clamp_scale, SCALES, CONTROL_ITEMS

CREAM='#fff8eb'; INK='#604333'; SAGE='#9eaf86'; PEACH='#edb399'

class App(ReferenceUI,RoomInteractions):
    def __init__(self,root):
        self.root=root; self.root.title('Little Companions • Development prototype')
        self.root.geometry('1480x940'); self.root.minsize(1260,860); self.root.configure(bg=CREAM)
        save_dir=Path(os.getenv('LOCALAPPDATA',str(Path.home()/'.local/share')))/'LittleCompanions'
        self.state=GameState(save_dir/'save.json')
        self.heading_font,self.body_font=install_fonts(root)
        self.reaction='idle'; self.until=0; self.last_activity=time.monotonic(); self.phase=0
        self.panel='Pet Space'; self.desktop=None; self.native_desktop=None; self.paused=False; self.global_input=False
        prefs=self.state.data['view_settings']
        self.room_scale=prefs['room_scale'];self.desktop_scale=prefs['desktop_scale']
        from rendering_cache import ImageCache
        self.scale_cache=ImageCache()
        self.init_interactions()
        self.desktop_interaction='click'
        self._last_window_state='normal'
        self.keys=set(); self.dirty=bool(self.state.migration_notice); self.last_save=0
        self.background=BackgroundInput(); self.hooked=False
        self.animation_started=time.monotonic(); self.animation_offset=0
        self.room_server=None; self.room_url=''; self.room_token=''; self.player_id=secrets.token_hex(16)
        self.remote=[]; self.net_queue=queue.Queue(); self.net_busy=False; self.net_generation=0
        self.asset_dir=Path(__file__).with_name('assets')
        self.load_art()
        self.notice=tk.StringVar(value=self.state.migration_notice or 'Welcome! Choose a pet, then type or click to earn your first gift.')
        self.stats=tk.StringVar(); self.banner=tk.StringVar(value='Solo • Your progress stays on this computer')
        self.build()
        self.root.bind('<KeyPress>',self.local_key)
        self.root.bind('<ButtonPress>',self.local_click,add='+')
        self.root.bind('<F11>',lambda e:self.fullscreen())
        self.root.protocol('WM_DELETE_WINDOW',self.close)
        if sys.platform=='win32':
            self.get_key=ctypes.windll.user32.GetAsyncKeyState
            self.get_key.argtypes=[ctypes.c_int]; self.get_key.restype=ctypes.c_short
            self.set_global_tracking(prefs['background_activity'])
        self.root.after(33 if self.state.data['view_settings'].get('low_power') else 16,self.tick)
        self.root.after(250,self.network_tick)
        if self.state.warning: messagebox.showwarning('Recovered save',self.state.warning)

    def button(self,parent,text,command,accent=False):
        b=CozyButton(parent,text,command,(self.body_font,10,'bold'),accent)
        b.pack(side='left',padx=4,pady=4);return b

    def select(self,pet):
        previous=self.state.data['pet']
        from live_panels import swapped_visitors
        self.visit_pets=swapped_visitors(getattr(self,'visit_pets',[p for p in PETS if p!=previous]),previous,pet)
        self.previewing_room=None;self.wander=None;self.spinning=False
        self.state.data['pet']=pet;self.dirty=True;self.show(self.panel)
    def rename(self):
        pet=self.state.data['pet']
        if self.state.data['coins']<30:self.notice.set('You need 30 leaves to rename your pet.');return
        name=simpledialog.askstring('Rename • 30 leaves','New name (1–24 characters). Changing it costs 30 leaves:',initialvalue=self.state.data['names'][pet],parent=self.root)
        if name is None:return
        if name.strip()==self.state.data['names'][pet]:return
        if not name.strip() or len(name.strip())>24:self.notice.set('Use a name of 1–24 characters.');return
        if messagebox.askyesno('Rename companion',f'Rename to {name.strip()} for 30 leaves?',parent=self.root):
            self.notice.set(self.state.rename_pet(pet,name));self.dirty=True;self.save();self.show(self.panel)
    def change_room(self,room):
        if self.state.switch_room(room):self.previewing_room=None;self.wander=None;self.spinning=False;self.dirty=True
    def decorate(self,item):
        if getattr(self,'previewing_room',None):return
        if item not in self.state.data['items']:self.notice.set('Unlock this item in Collection first.');return
        from decoration_inventory import placed_here
        result=self.state.remove_decoration(item) if placed_here(self.state.data,item) else self.state.place_decoration(item)
        self.notice.set(result);self.dirty=True
    def equip(self,item):
        d=self.state.data;p=d['pet']
        if not item:
            d['wardrobe'].setdefault(p,{}).pop('outfit',None);d['accessory'][p]='';self.dirty=True;return
        if item not in d['items'] or not available(item,p):
            self.notice.set('Choose clothing made for '+d['names'][p]+'.');return
        from accessory_layers import MODULAR,equip_accessory,HEAD_CONFLICTS
        if item in MODULAR:
            self.notice.set(equip_accessory(d,p,item));self.dirty=True;return
        slot=CATALOG[item]['slot'];slots=d['wardrobe'].setdefault(p,{})
        if item in equipped(d,p):slots.pop(slot,None);value=''
        else:
            slots[slot]=item;value=item
            if item in HEAD_CONFLICTS:slots.pop('head',None)
        if slot=='accessory':d['accessory'][p]=value
        self.dirty=True;self.notice.set(('Wearing ' if value else 'Removed ')+item+'.')
    def item_action(self,item):
        if item in ACCESSORIES and item in self.state.data['items']:self.equip(item);return
        self.notice.set(self.state.buy(item));self.dirty=True;self.show(self.panel)
    def open_gift(self,all_gifts=False):
        if getattr(self,'gift_batch',False) or getattr(self,'gift_busy',False) or getattr(self,'gift_close_at',0)>time.monotonic():return
        count=self.state.data['gifts'] if all_gifts else min(1,self.state.data['gifts'])
        if not count:return
        self.gift_busy=True
        try:
            self.gift_results=self.state.open_gifts(count);self.gift_index=0;self.gift_result=self.gift_results[0]
            self.gift_batch=count>1;self.gift_started=time.monotonic()
            self.gift_reveal_at=self.gift_started+(.12 if self.state.data['view_settings'].get('reduced_effects') else .9)
            self.gift_close_at=self.gift_reveal_at+2.4
            self.notice.set(f'Opened {count} gift(s). All prizes saved; +{15*count} leaves.')
            self.dirty=True;self.save();self.show('Rewards')
        finally:self.gift_busy=False

    def next_gift_prize(self,step):
        if time.monotonic()<self.gift_reveal_at or not getattr(self,'gift_results',[]):return
        self.gift_index=(self.gift_index+step)%len(self.gift_results);self.gift_result=self.gift_results[self.gift_index]
        if getattr(self,'gift_canvas',None):
            from comfort import draw_gift
            draw_gift(self,time.monotonic())

    def close_gift_batch(self):
        if time.monotonic()<getattr(self,'gift_reveal_at',0):return
        self.gift_batch=False;self.gift_result=None;self.gift_close_at=0;self.gift_reveal_at=0;self.show('Rewards')

    def update_gift_reveal(self,now):
        if not getattr(self,'gift_batch',False) and getattr(self,'gift_close_at',0) and now>=self.gift_close_at:
            self.gift_result=None;self.gift_reveal_at=0;self.gift_close_at=0
    def animation_frame(self,now=None):
        now=time.monotonic() if now is None else now
        period=.18 if self.reaction in ('heart','wave') else .14
        return (self.animation_offset+int(max(0,now-self.animation_started)/period))%4

    def start_sleep(self):
        self.manual_sleep=True;self.wander=None;self.spinning=False;self.pointer=None;self.hover_zone=None
        self.reaction='sleep';self.until=0;self.render_animals();self.notice.set('Sleep time. Choose Idle or pet your companion to wake them.')

    def toggle_taskbar_run(self):
        prefs=self.state.data['view_settings'];prefs['taskbar_running']=not prefs.get('taskbar_running',True);self.dirty=True
        self.notice.set('Taskbar running '+('on' if prefs['taskbar_running'] else 'off'));self.save()

    def start_idle(self):
        self.manual_sleep=False
        if getattr(self,'previewing_room',None):self.close_preview()
        self.set_interaction_mode('click');self.pointer=None;self.hover_zone=None;self.spinning=False
        self.wander=None;now=time.monotonic();self.last_activity=now-6
        self.reaction='idle';self.until=0;self.animation_started=now;self.animation_offset=0
        self.manual_idle_until=now+.3
        self.update_wander(now);self.render_animals();self.notice.set('Idle time • Your pet can explore the room.')

    def activity(self,count=1,reaction='typing'):
        now=time.monotonic()
        if not self.paused:
            bonus=self.state.activity(count,'keystrokes' if reaction=='typing' else 'clicks');self.dirty=True
            if bonus:self.notice.set(f'1,000 activities! +{bonus} free leaves added.')
        if reaction=='click' and now<getattr(self,'manual_idle_until',0):return
        if not getattr(self,'manual_sleep',False):self.start_reaction(reaction,now,count)

    def start_reaction(self,reaction,now=None,count=1):
        if reaction in ('pet','toy','heart'):self.manual_sleep=False
        elif getattr(self,'manual_sleep',False):return
        now=time.monotonic() if now is None else now
        play=('heart','wave')
        continuing=now<self.until and (self.reaction==reaction or self.reaction in play and reaction in play)
        if not continuing:
            self.animation_offset=1 if reaction in ('pet','toy') else 0;self.animation_started=now
        # Repeated clicks refresh affection without skipping the paw's return.
        self.last_activity=now;self.reaction=reaction;self.until=now+.84

    def interact(self,reaction,count=True):
        if not self.global_input and count:self.activity(reaction=reaction)
        else:self.start_reaction(reaction)
        self.until=self.last_activity+2
        self.render_animals()

    def local_key(self,event):
        if not self.global_input and not isinstance(event.widget,(tk.Entry,ttk.Combobox)) and event.keysym not in ('F11','Shift_L','Shift_R','Control_L','Control_R','Alt_L','Alt_R'):
            self.activity()
            self.render_animals()

    def local_click(self,event):
        # When background tracking is disabled, ordinary interface clicks still
        # count. Direct pet actions supply their own activity event.
        if not self.global_input and not self.paused:
            self.state.activity(1,'clicks')
            self.dirty=True

    def toggle_pause(self):self.paused=self.pause_var.get()
    def toggle_global(self):
        self.background.stop();self.hooked=False
        self.set_global_tracking(self.global_var.get())

    def set_global_tracking(self,enabled):
        self.background.stop();self.hooked=False
        self.global_input=bool(enabled and sys.platform=='win32');self.keys=set()
        self.state.data['view_settings']['background_activity']=bool(enabled);self.dirty=True
        if self.global_input:
            try:self.hooked=self.background.start()
            except OSError:self.hooked=False;self.background.stop()
            if not self.hooked:self.notice.set('Windows event hooks unavailable; using fast activity polling.')
    def fullscreen(self):self.fullscreen_room()
    def save(self):
        try:self.state.save();self.dirty=False;self.last_save=time.monotonic()
        except OSError as exc:
            self.notice.set(f'Could not save progress: {exc}')
            if hasattr(self,'debug'):self.debug.caught('Save failure',exc)

    def set_pet_scale(self,value,desktop=False):
        value=clamp_scale(value)
        if desktop:
            self.desktop_scale=value
            if getattr(self,'native_desktop',None):
                self.native_desktop.return_home_requested=True;self.native_desktop.group_adjust_until=time.monotonic()+3
        else:self.room_scale=value;self.scale_cache.clear()
        self.state.data['view_settings']['desktop_scale' if desktop else 'room_scale']=value
        self.dirty=True
        if hasattr(self,'size_label'):self.size_label.configure(text=f'{self.room_scale}%')
        self.render_animals()

    def change_desktop_scale(self,delta):
        self.set_pet_scale(self.desktop_scale+delta,desktop=True)

    def desktop_mode(self):
        self.spinning=False
        if self.room_window:self.close_room()
        if sys.platform=='win32':
            try:
                if self.native_desktop is None:self.native_desktop=DesktopOverlay(self)
                self.native_desktop.show()
            except OSError as exc:
                self.notice.set(f'Could not open transparent companion: {exc}')
                if hasattr(self,'debug'):self.debug.caught('Desktop startup failure',exc)
                return
            self._last_window_state='iconic'
            self.root.iconify()
            first,second=CONTROL_ITEMS[self.state.data['pet']]
            self.notice.set(f'Desktop: left {first.replace("-"," ")} returns home; right {second.replace("-"," ")} hides. Scroll to resize; right-click for options.')
            return
        # Other platforms keep the framed Tk window; per-pixel overlay is Windows-only.
        if self.desktop and self.desktop.winfo_exists():self.desktop.deiconify();return
        self.desktop=tk.Toplevel(self.root);self.desktop.title('Companion');self.desktop.geometry('380x390')
        self.desktop.attributes('-topmost',True);self.desktop.configure(bg=CREAM)
        self.desktop_canvas=tk.Canvas(self.desktop,bg=CREAM,highlightthickness=0);self.desktop_canvas.pack(fill='both',expand=True)
        self.desktop_canvas.bind('<ButtonPress-1>',self.drag_start);self.desktop_canvas.bind('<B1-Motion>',self.drag)
        self.desktop_canvas.bind('<ButtonRelease-1>',lambda e:self.interact('heart'))
        wallet=tk.Frame(self.desktop,bg=CREAM);wallet.pack()
        self.desktop_balances={}
        for key,name in [('coins','leaves'),('moonstones','moonstones'),('clicks',None),('keystrokes',None)]:
            label=self.label(wallet,'',11,True,bg=CREAM,image=self.currency_art[name] if name else '',compound='left')
            label.pack(side='left',padx=8);self.desktop_balances[key]=label
        row=tk.Frame(self.desktop,bg=CREAM);row.pack()
        self.button(row,'Pet space',self.return_to_pet_space);self.button(row,'Hide',self.hide_desktop)
        self.root.iconify()

    def return_to_pet_space(self):
        if self.native_desktop:self.native_desktop.hide()
        if self.desktop and self.desktop.winfo_exists():self.desktop.withdraw()
        self.pointer=None;self.held=False
        self.root.deiconify();self.show('Pet Space');self.root.lift();self.root.focus_force()

    def hide_desktop(self):
        if self.native_desktop:self.native_desktop.hide()
        if self.desktop and self.desktop.winfo_exists():self.desktop.withdraw()
        # Main game remains on taskbar; activity tracking continues while hidden.
        self.notice.set('Companion hidden. Restore the game from the taskbar to show it again.')

    def desktop_menu(self):
        menu=CozyMenu(self.root,tearoff=False)
        menu.add_command(label='Back to Pet Space',command=self.return_to_pet_space)
        menu.add_command(label='Hide companion',command=self.hide_desktop)
        menu.add_command(label='Sleep',command=self.start_sleep)
        menu.add_command(label='Wake / Idle',command=self.start_idle)
        menu.add_command(label=('Stop taskbar running' if self.state.data['view_settings'].get('taskbar_running',True) else 'Run along taskbar'),command=self.toggle_taskbar_run)
        menu.add_separator()
        for title,mode in [('Click / drag pet','click'),('Pet with hand','pet'),('Play with toy','toy')]:
            menu.add_command(label=title,command=lambda m=mode:setattr(self,'desktop_interaction',m))
        menu.add_separator()
        for size in SCALES:menu.add_command(label=f'Pet size: {size}%',command=lambda n=size:self.set_pet_scale(n,desktop=True))
        try:menu.tk_popup(self.root.winfo_pointerx(),self.root.winfo_pointery())
        finally:menu.grab_release()

    def drag_start(self,e):self.drag_origin=(e.x_root-self.desktop.winfo_x(),e.y_root-self.desktop.winfo_y())
    def drag(self,e):self.desktop.geometry(f'+{max(0,e.x_root-self.drag_origin[0])}+{max(0,e.y_root-self.drag_origin[1])}')

    def current_pose(self):
        return {'typing':'typing','sleep':'sleep','heart':'play','wave':'play'}.get(self.reaction,'idle')

    def sync_desktop_visibility(self):
        if sys.platform!='win32':return
        current=self.root.state()
        previous=getattr(self,'_last_window_state',current)
        self._last_window_state=current
        if current=='iconic' and previous!='iconic' and self.state.data['view_settings'].get('auto_desktop',True):self.desktop_mode()
        elif previous=='iconic' and current in ('normal','zoomed'):
            if getattr(self,'native_desktop',None):self.native_desktop.hide()
            if getattr(self,'desktop',None) and self.desktop.winfo_exists():self.desktop.withdraw()

    def tick(self):
        self.sync_desktop_visibility()
        now=time.monotonic();self.phase+=.13
        self.refresh_season(now)
        self.update_gift_reveal(now)
        if getattr(self,'native_desktop',None):self.native_desktop.drain_actions()
        if self.global_input and sys.platform=='win32':
            if self.hooked and not self.background.running:
                self.hooked=False
                self.notice.set('Activity listener stopped; using fast activity polling.')
            if self.hooked:
                for reaction in self.background.drain():
                    # Preserve a direct pet-button reaction while counting the click.
                    direct_click=self.reaction in ('heart','pet','toy','click') and now<self.until
                    if direct_click:
                        if not self.paused:self.state.activity(1,'keystrokes' if reaction=='typing' else 'clicks');self.dirty=True
                    else:self.activity(reaction='click' if reaction=='wave' else reaction)
            else:
                down={k for k in [1,2,4]+list(range(8,256)) if k not in (16,17,18,160,161,162,163,164,165) and self.get_key(k)&0x8000}
                pressed=down-self.keys;self.keys=down
                for key in pressed:self.activity(reaction='click' if key in (1,2,4) else 'typing')
        if getattr(self,'pointer',None):self.refresh_pointer_reaction()
        self.update_wander(now)
        if getattr(self,'manual_sleep',False):self.reaction='sleep'
        elif now>self.until:self.reaction='sleep' if now-self.last_activity>25 and not getattr(self,'wander',None) else 'idle'
        d=self.state.data;self.stats.set(f"{d['coins']} leaves   •   {d['gifts']} gifts   •   Next gift {d['points']}/{GIFT_THRESHOLD}"+('   •   Paused' if self.paused else ''))
        self.render_animals()
        from comfort import update_lifetime
        update_lifetime(self)
        if self.dirty and now-self.last_save>5:self.save()
        self.root.after(33 if self.state.data['view_settings'].get('low_power') else 16,self.tick)

    def host(self):
        self.leave()
        try:self.room_server=RoomServer()
        except OSError as exc:self.notice.set(f'Cannot host: {exc}');return
        self.room_url=f'http://127.0.0.1:{self.room_server.port}';self.room_token=self.room_server.token
        self.banner.set('Private LAN room • Waiting for a friend');self.show('Friends')
    def join(self):
        host=simpledialog.askstring('Join friend','Host’s local IPv4 address (example: 192.168.1.20):')
        if not host:return
        import ipaddress
        try:
            address=ipaddress.IPv4Address(host.strip())
            if not address.is_private:raise ValueError()
        except ValueError:self.notice.set('Use a local-network IPv4 address.');return
        token=simpledialog.askstring('Private invitation','Paste your friend’s invite token:')
        if not token:return
        self.leave();self.room_url=f'http://{address}:47832';self.room_token=token.strip();self.banner.set('Connecting to private LAN room…')
    def leave(self):
        self.net_generation+=1;self.room_url='';self.room_token='';self.remote=[]
        if self.room_server:
            server=self.room_server;self.room_server=None;threading.Thread(target=server.close,daemon=True).start()
        self.banner.set('Solo • Your progress stays on this computer')
    def network_tick(self):
        while not self.net_queue.empty():
            generation,result,error=self.net_queue.get();self.net_busy=False
            if generation!=self.net_generation:continue
            if error:
                self.remote=[]
                self.banner.set('Friend connection unavailable • Solo progress continues')
            else:
                self.remote=result;self.banner.set(f'Private LAN room • {len(result)}/2 players')
        if self.panel=='Friends' and hasattr(self,'friend_label'):
            self.friend_label.configure(text='\n'.join(f"{p['name']} • {p['reaction']}" for p in self.remote) or 'No connected companions yet.')
        if self.room_url and not self.net_busy:
            self.net_busy=True;generation=self.net_generation;url=self.room_url;token=self.room_token;d=self.state.data;p=d['pet']
            payload=dict(id=self.player_id,pet=p,name=d['names'][p],room=d['pet_rooms'][p],reaction=self.reaction)
            def run():
                try:self.net_queue.put((generation,exchange(url,token,payload),''))
                except Exception as exc:self.net_queue.put((generation,[],str(exc)))
            threading.Thread(target=run,daemon=True).start()
        self.root.after(250,self.network_tick)
    def close(self):
        self.background.stop()
        if self.native_desktop:self.native_desktop.close()
        self.save();self.leave();self.root.destroy()

if __name__=='__main__':
    from launcher import main
    raise SystemExit(main())
