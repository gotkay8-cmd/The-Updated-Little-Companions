"""Interactive pet model and individual purchase controls in the wardrobe."""
import tkinter as tk
from time import monotonic
from wardrobe_model import WardrobeDraft
from wardrobe import SLOTS
from model import PETS, price_label, price_for, shop_available
from cozy_ui import CozyButton, CozyChoice, selection_row
from outfit_preview import Playback, MOTIONS, set_caption
from png_scaling import resized_png

CREAM = '#fff8eb'
INK = '#604333'


class FittingRoom:
    def __init__(self, app):
        self.app = app
        data = app.state.data
        pet = getattr(app, 'wardrobe_group', data['pet'])
        if pet not in PETS:
            pet = data['pet']
        self.draft = WardrobeDraft(data, pet)
        self.photos = {}
        self.last_paths = None
        self.timer = None
        self.closed = False
        from layered_animation import preview_timing
        self.playback = Playback(lambda motion:preview_timing(app.art_dir,self.draft.pet,motion))
        self.playback.showcase = False
        self.playback.playing = not data.get('view_settings', {}).get('reduced_effects', False)
        self.last_time = monotonic()
        self.frame = tk.Frame(app.content, bg=CREAM)
        self.frame.pack(fill='both', expand=True)
        self.frame.bind('<Destroy>', self.close)
        font = (app.body_font, 10, 'bold')
        tk.Label(self.frame, text='Try a little something cozy', bg=CREAM, fg=INK,
                 font=(app.heading_font, 17, 'bold')).pack(pady=6)
        selection_row(app, self.frame, [(data['names'].get(p, p), lambda p=p:app.choose_wardrobe(p), p == pet)
                                        for p in PETS])
        self.balance = tk.Label(self.frame, bg=CREAM, fg=INK, font=font)
        self.balance.pack(pady=4)
        body = tk.Frame(self.frame, bg=CREAM)
        body.pack(fill='both', expand=True, padx=12)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        model = tk.Frame(body, bg=CREAM)
        model.grid(row=0, column=0, sticky='nsew', padx=8)
        self.canvas = tk.Canvas(model, width=360, height=360, bg=CREAM, highlightthickness=0)
        self.canvas.pack(expand=True)
        self.fit_note=tk.Label(model,text='',bg=CREAM,fg=INK,wraplength=350,font=(app.body_font,9))
        self.fit_note.pack()
        controls = tk.Frame(model, bg=CREAM)
        controls.pack(pady=4)
        CozyChoice(controls, 'Idle', list(MOTIONS), self.motion, font).pack(side='left', padx=4)
        self.pause = CozyButton(controls, 'Pause' if self.playback.playing else 'Play', self.toggle, font)
        self.pause.pack(side='left', padx=4)
        right = tk.Frame(body, bg=CREAM)
        right.grid(row=0, column=1, sticky='nsew', padx=8)
        self.labels = {}
        self.buttons = {}
        self.arrows = {}
        for slot, title in zip(SLOTS, ('Outfit', 'Hat or bow', 'Collar or bandana', 'Charm')):
            row = tk.Frame(right, bg=CREAM)
            row.pack(fill='x', pady=3)
            titlebar = tk.Frame(row, bg=CREAM)
            titlebar.pack(fill='x')
            tk.Label(titlebar, text=title, bg=CREAM, fg=INK, font=font).pack(side='left')
            button = CozyButton(titlebar, 'Owned', lambda s=slot:self.buy(s), font)
            button.pack(side='right', pady=2)
            choices = tk.Frame(row, bg=CREAM)
            choices.pack(fill='x')
            left = CozyButton(choices, '‹', lambda s=slot:self.cycle(s, -1), font)
            left.pack(side='left')
            label = tk.Label(choices, bg=CREAM, fg=INK, wraplength=215, width=25,
                             font=(app.body_font, 10))
            label.pack(side='left', fill='x', expand=True, padx=5)
            arrow = CozyButton(choices, '›', lambda s=slot:self.cycle(s, 1), font)
            arrow.pack(side='left')
            self.arrows[slot] = (left, arrow)
            self.labels[slot] = label
            self.buttons[slot] = button
        footer = tk.Frame(self.frame, bg=CREAM)
        footer.pack(fill='x', padx=16, pady=8)
        self.status = tk.Label(footer, bg=CREAM, fg=INK, wraplength=650, font=(app.body_font, 10))
        self.status.pack()
        actions = tk.Frame(footer, bg=CREAM)
        actions.pack(pady=4)
        self.wear = CozyButton(actions, 'Wear this look', self.apply, font, accent=True)
        self.wear.pack(side='left', padx=4)
        CozyButton(actions, 'Reset to wearing', self.reset, font).pack(side='left', padx=4)
        CozyButton(actions, 'Try storybook look', self.storybook, font).pack(side='left', padx=4)
        self.refresh()
        self.tick()

    def refresh(self):
        data = self.app.state.data
        self.balance.configure(text=f"{data['coins']} leaves  •  {data.get('moonstones', 0)} Moonstones")
        for slot in SLOTS:
            item = self.draft.slots.get(slot)
            self.labels[slot].configure(text=item or 'None')
            button = self.buttons[slot]
            if not item or item in data['items']:
                set_caption(button, 'Owned' if item else 'Nothing selected')
                button.configure(state='disabled')
            else:
                currency, cost = price_for(item)
                set_caption(button, 'Buy • ' + price_label(item))
                button.configure(state='normal' if shop_available(item) and data.get(currency, 0) >= cost else 'disabled')
            enabled = len(self.draft.options(slot, data)) > 1
            for arrow in self.arrows[slot]:
                arrow.configure(state='normal' if enabled else 'disabled')
        missing = self.draft.missing(data)
        self.wear.configure(state='disabled' if missing else 'normal')
        self.status.configure(text=('Preview only • buy selected items above to wear this look.' if missing
                                   else 'Preview only • choose Wear this look to save your selections.') +
                              (' Charms need a collar.' if self.draft.slots.get('neck') not in ('Meadow Collar', 'Midnight Collar') else '') +
                              ' Outfits with built-in hats allow bows; extra hats are unavailable.')
        self.last_paths = None

    def cycle(self, slot, step):
        self.draft.cycle(slot, step, self.app.state.data)
        self.refresh()
        self.render()

    def storybook(self):
        from approved_art import approved_slots
        self.draft.slots = approved_slots(self.draft.pet)
        self.refresh()
        self.status.configure(text='A coordinated flower, collar and acorn look. Unfinished layers remain hidden for that motion; purchases stay saved.')
        self.render()

    def buy(self, slot):
        item = self.draft.slots.get(slot)
        if not item or item in self.app.state.data['items']:
            return
        result = self.app.state.buy(item)
        self.app.notice.set(result)
        self.app.dirty = True
        self.app.save()
        self.refresh()
        self.status.configure(text=result + ' Your preview is ready; Wear this look saves it.')

    def apply(self):
        if self.draft.apply(self.app.state.data):
            self.app.dirty = True
            self.app.save()
            self.app.last_dynamic = None
            self.refresh()
            self.status.configure(text='This look is now worn by ' + self.app.state.data['names'][self.draft.pet] + '.')

    def reset(self):
        self.draft = WardrobeDraft(self.app.state.data, self.draft.pet)
        self.refresh()
        self.render()

    def motion(self, value):
        self.playback.select(value)
        self.last_paths = None
        self.render()

    def toggle(self):
        self.playback.playing = not self.playback.playing
        set_caption(self.pause, 'Pause' if self.playback.playing else 'Play')

    def render(self):
        paths = tuple(self.draft.paths(self.app.art_dir, self.playback.motion, self.playback.frame))
        hidden=self.draft.slots.get('outfit') and 'layered-motions' in paths[0].parts and not any(
            p.parent.name==self.draft.slots['outfit'].lower().removeprefix(self.draft.pet.lower()+' ').removesuffix(' outfit').replace(' ','-') for p in paths[1:])
        self.fit_note.configure(text='This outfit is still being fitted for this motion. Your purchase stays saved.' if hidden else '')
        if paths == self.last_paths:
            return
        if len(self.photos) > 180:
            self.photos.clear()
        self.canvas.delete('pet')
        for path in paths:
            if path not in self.photos:
                self.photos[path] = (tk.PhotoImage(master=self.frame,file=str(path)) if 'layered-motions' in path.parts or 'layered-walk' in path.parts
                                    else tk.PhotoImage(master=self.frame,data=resized_png(path,360,310)))
            self.canvas.create_image(180,360,anchor='s',image=self.photos[path],tags='pet')
        self.last_paths = paths

    def tick(self):
        if self.closed:
            return
        now = monotonic()
        self.playback.advance(min(now - self.last_time, .25))
        self.last_time = now
        self.render()
        self.timer = self.frame.after(20, self.tick)

    def close(self, event):
        if event.widget != self.frame:
            return
        self.closed = True
        if self.timer:
            self.frame.after_cancel(self.timer)


def build_fitting_room(app):
    app.wardrobe_fitting = FittingRoom(app)
