"""Read-only wardrobe theatre using the game's actual fitted sprite frames."""
import tkinter as tk
from time import monotonic
from wardrobe import CATALOG, outfit_sprite, OUTFIT_ANGLES
from cozy_ui import CozyButton, CozyChoice
from cozy_dialogs import window
from model import price_label

MOTIONS = ('Idle', 'Petting', 'Playing', 'Sleeping', 'Clicking', 'Typing',
           'Toy reaction', 'Walk left', 'Walk right', 'Walk up', 'Walk down',
           'Run left', 'Run right', 'Turn around')
REACTIONS = dict(zip(MOTIONS[:7], ('idle','pet','play','sleep','click','typing','toy')))

class Playback:
    def __init__(self, timing_resolver=None):
        self.timing_resolver=timing_resolver
        self.motion = MOTIONS[0]
        self.frame = 0
        self.elapsed = 0.0
        self.showcase = True
        self.playing = True

    @property
    def count(self):
        if self.timing_resolver:return self.timing_resolver(self.motion)[0]
        if self.motion in ('Walk left','Walk right'):return 9
        return 8 if self.motion.startswith('Run') or self.motion == 'Turn around' else 4

    @property
    def interval(self):
        if self.timing_resolver:return self.timing_resolver(self.motion)[1]
        if self.motion in ('Walk left','Walk right'):return .09
        return .09 if self.motion.startswith('Run') else .16 if self.motion.startswith('Walk') else .24

    def select(self, motion):
        self.motion = motion
        self.frame = 0
        self.elapsed = 0.0

    def advance(self, seconds):
        if not self.playing: return
        self.elapsed += max(0, seconds)
        if self.showcase and self.elapsed >= 3.84:
            remainder = self.elapsed % 3.84
            self.select(MOTIONS[(MOTIONS.index(self.motion) + 1) % len(MOTIONS)])
            self.elapsed = remainder
        if self.motion=='Idle' and self.timing_resolver:
            phase=self.elapsed%2.71
            self.frame=0 if phase<2.2 else 1 if phase<2.38 else 2 if phase<2.53 else 3
        else:self.frame = int(self.elapsed / self.interval) % self.count

    def step(self):
        self.playing = False
        self.frame = (self.frame + 1) % self.count
        self.elapsed = self.frame * self.interval


def preview_sprite(art_dir, item, motion, frame):
    pet = CATALOG[item]['pet']
    if pet is None:
        return accessory_preview_paths(art_dir,{'pet':'Mochi','items':[],'wardrobe':{}},item,motion,frame)[0]
    data = {'items': [item], 'wardrobe': {pet: {'outfit': item}}}
    kwargs = {}
    if motion.startswith('Walk '): kwargs['walking'] = motion.split()[1]
    if motion.startswith('Run '): kwargs['running'] = motion.split()[1]
    if motion == 'Turn around': kwargs['facing'] = OUTFIT_ANGLES[frame % 8]
    return outfit_sprite(art_dir, data, pet, REACTIONS.get(motion, 'idle'), frame, **kwargs)


def accessory_preview_paths(art_dir,data,item,motion,frame):
    from copy import deepcopy
    from pathlib import Path
    from accessory_layers import MODULAR,COLLARS,equip_accessory,layer_paths,HEAD_CONFLICTS
    draft=deepcopy(data);pet=draft['pet'];slots=draft.setdefault('wardrobe',{}).setdefault(pet,{})
    draft.setdefault('items',[])
    if item not in draft['items']:draft['items'].append(item)
    if MODULAR[item]['slot']=='charm' and slots.get('neck') not in COLLARS:
        slots['neck']='Meadow Collar';draft['items'].append('Meadow Collar')
    # Preview without toggling off an already equipped item.
    if slots.get(MODULAR[item]['slot'])==item:slots.pop(MODULAR[item]['slot'])
    equip_accessory(draft,pet,item)
    kwargs={};name=REACTIONS.get(motion,'idle')+'-'+str(frame%4)
    if motion.startswith('Walk '):kwargs['walking']=motion.split()[1];name='walk-'+kwargs['walking']+'-'+str(frame%4)
    if motion.startswith('Run '):kwargs['running']=motion.split()[1];name='run-'+kwargs['running']+'-'+str(frame%8)
    if motion=='Turn around':
        from wardrobe import turn_angles
        angles=turn_angles(draft,pet);angle=angles[frame%len(angles)];kwargs['facing']=angle
        name='turn-'+str(angle) if angle else 'idle-0'
    base=outfit_sprite(art_dir,draft,pet,REACTIONS.get(motion,'idle'),frame,**kwargs)
    if base is None:
        filename=pet.lower()+'-'+name+'.png' if name.startswith(('walk','run','turn')) else pet.lower()+'_'+name.replace('-','_')+'.png'
        base=Path(art_dir)/filename
    return [base]+layer_paths(art_dir,draft,pet,base)


def set_caption(button, text):
    if button.caption == text: return
    button.caption = text
    button.width = max(45, button.textfont.measure(text) + 30)
    button.configure(width=button.width)


class OutfitPreview:
    def __init__(self, app, item):
        self.app = app
        self.item = item
        from layered_animation import preview_timing
        self.playback = Playback(lambda motion:preview_timing(app.art_dir,CATALOG[self.item]['pet'] or app.state.data['pet'],motion))
        self.photos = {}
        self.after_id = None
        self.closed = False
        self.last_path = None
        self.last_controls = None
        self.win, body = window(app.root, 'The cozy dressing room', '700x720')
        self.win.resizable(False, False)
        self.win.bind('<Destroy>', self.destroyed, add='+')
        font = (app.body_font, 10, 'bold')
        self.title = tk.Label(body, bg='#fff8eb', fg='#604333', font=(app.heading_font, 15, 'bold'))
        self.title.pack()
        self.details = tk.Label(body, bg='#fff8eb', fg='#80654e', font=(app.body_font, 10))
        self.details.pack(pady=4)
        self.canvas = tk.Canvas(body, width=640, height=380, bg='#f3e6d1', highlightthickness=1, highlightbackground='#dfc7a6')
        self.canvas.pack(pady=6)
        self.canvas.create_oval(145,325,495,365,fill='#e4d2b6',outline='')
        self.sprite = self.canvas.create_image(320, 365, anchor='s')
        self.status = tk.Label(body, bg='#fff8eb', fg='#604333', font=font)
        self.status.pack()
        choices = tk.Frame(body, bg='#fff8eb'); choices.pack(pady=4)
        self.choice = CozyChoice(choices, MOTIONS[0], MOTIONS, self.choose, font)
        self.choice.pack(side='left', padx=4)
        self.auto = CozyButton(choices, 'Showcase: on', self.toggle_showcase, font)
        self.auto.pack(side='left', padx=4)
        controls = tk.Frame(body,bg='#fff8eb'); controls.pack()
        self.pause = CozyButton(controls, 'Pause', self.toggle_play, font)
        self.pause.pack(side='left',padx=4)
        CozyButton(controls, 'Next frame', self.step, font).pack(side='left',padx=4)
        navigation = tk.Frame(body,bg='#fff8eb'); navigation.pack(pady=4)
        CozyButton(navigation,'‹ Previous outfit',lambda:self.change(-1),font).pack(side='left',padx=4)
        CozyButton(navigation,'Next outfit ›',lambda:self.change(1),font).pack(side='left',padx=4)
        tk.Label(body,text='Preview only • clothing and accessories use separate fitted layers',bg='#fff8eb',fg='#80654e',font=(app.body_font,9)).pack(pady=3)
        self.refresh_title()
        self.last_tick = monotonic()
        self.tick()

    def refresh_title(self):
        pet = CATALOG[self.item]['pet'] or self.app.state.data['pet']
        data = self.app.state.data
        self.title.configure(text=self.item)
        owned = 'Owned' if self.item in data['items'] else price_label(self.item)
        from accessory_layers import MODULAR,head_conflict
        note=''
        if self.item in MODULAR:
            slot=MODULAR[self.item]['slot']
            if slot=='head' and head_conflict(data.get('wardrobe',{}).get(pet,{}),self.item):note=' • Outfit has a painted-in hat; ear bows fit'
            elif slot=='charm':note=' • Collar required (shown in preview)'
        self.details.configure(text=f"{data['names'].get(pet,pet)} • {owned}"+note)

    def change(self, direction):
        items = list(CATALOG)
        self.item = items[(items.index(self.item) + direction) % len(items)]
        self.photos.clear()  # Bound memory to one outfit, not the entire wardrobe.
        self.last_path = None
        self.refresh_title()
        self.render()

    def choose(self, motion):
        self.playback.select(motion)
        self.playback.showcase = False
        self.render()

    def toggle_showcase(self):
        self.playback.showcase = not self.playback.showcase
        self.playback.elapsed = self.playback.frame * self.playback.interval
        self.render()

    def toggle_play(self):
        self.playback.playing = not self.playback.playing
        self.last_tick = monotonic()
        self.render()

    def step(self):
        self.playback.step()
        self.render()

    def render(self):
        p = self.playback
        from accessory_layers import MODULAR,HEAD_CONFLICTS
        if self.item in MODULAR:
            paths=accessory_preview_paths(self.app.art_dir,self.app.state.data,self.item,p.motion,p.frame)
        else:
            from wardrobe_model import WardrobeDraft
            pet=CATALOG[self.item]['pet']
            draft=WardrobeDraft({'wardrobe':{pet:{'outfit':self.item}}},pet)
            paths=draft.paths(self.app.art_dir,p.motion,p.frame)
        if tuple(paths)!=self.last_path:
            self.canvas.delete('accessory-preview')
            for i,path in enumerate(paths):
                if path not in self.photos:
                    if len(self.photos)>280:self.photos.clear()
                    self.photos[path]=tk.PhotoImage(master=self.win,file=str(path))
                if i==0:self.canvas.itemconfigure(self.sprite,image=self.photos[path])
                else:self.canvas.create_image(320,365,anchor='s',image=self.photos[path],tags='accessory-preview')
            self.last_path=tuple(paths)
        controls = (p.motion, p.frame, p.showcase, p.playing)
        if controls != self.last_controls:
            self.status.configure(text=f'{p.motion} • Frame {p.frame + 1}/{p.count}')
            set_caption(self.choice, p.motion+'  ▾')
            set_caption(self.auto, 'Showcase: '+('on' if p.showcase else 'off'))
            set_caption(self.pause, 'Pause' if p.playing else 'Play')
            self.last_controls = controls

    def tick(self):
        if self.closed: return
        now = monotonic()
        self.playback.advance(min(now - self.last_tick, .25))
        self.last_tick = now
        self.render()
        self.after_id = self.win.after(20, self.tick)

    def destroyed(self, event):
        if event.widget != self.win: return
        self.closed = True
        if self.after_id is not None:
            self.win.after_cancel(self.after_id)
            self.after_id = None
        self.photos.clear()


def open_preview(app, item):
    previous = getattr(app, '_outfit_preview', None)
    if previous is not None and not previous.closed:
        previous.win.destroy()
    app._outfit_preview = OutfitPreview(app, item)
