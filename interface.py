"""Illustrated UI, matching the approved three-column Pet Space composition."""
import sys
from decoration_inventory import item_name,placed_here
from wardrobe import equipped,outfit_sprite,OUTFITS
import time
import tkinter as tk
from tkinter import ttk
from cozy_ui import ornament,sprig
from model import PETS, THEMES, ITEMS, GIFT_THRESHOLD, SIGNATURE_ITEMS, DECORATIONS, ACCESSORIES, price_label, DEFAULT_TOYS

CREAM='#fff8eb'; INK='#604333'; SAGE='#9eaf86'; PEACH='#edb399'; BORDER='#ead8bd'; PANEL='#fffcf4'
ROOM_FILES=dict(zip(THEMES[:4],['cozy-nook','toy-room','pocket-garden','woodland']))
ROOM_FILES.update({'Seaside':'seaside','Starlight Attic':'starlight-attic','Blossom Conservatory':'blossom-conservatory','Pumpkin Parlor':'pumpkin-parlor'})

class VisualUI:
    def load_art(self):
        self.art_dir=self.asset_dir/'v5'
        self.art_paths={}
        def photo(name):
            path=self.art_dir/name;image=tk.PhotoImage(file=str(path));self.art_paths[str(image)]=path;return image
        from layered_animation import timing
        self.motion_art={p:{m:[photo(outfit_sprite(self.art_dir,{},p,m,i)) for i in range(timing(self.art_dir,p,m)[0])] for m in ('idle','typing','play','sleep','click','pet','toy')} for p in PETS}
        self.pet_art={p:{m:frames[0] for m,frames in motions.items()} for p,motions in self.motion_art.items()}
        self.typing_art={p:self.motion_art[p]['typing'] for p in PETS}
        self.walk_art={p:{direction:[photo(outfit_sprite(self.art_dir,{},p,'idle',i,walking=direction)) for i in range(timing(self.art_dir,p,walking=direction)[0])] for direction in ('left','right','up','down')} for p in PETS}
        self.turn_art={p:{angle:photo(outfit_sprite(self.art_dir,{},p,'idle',0,facing=angle)) for angle in (90,135,180,225,270)} for p in PETS}
        self.mochi_bare=self.motion_art['Mochi']
        from model import CUSHIONS
        self.seat_art={item:photo('seat-'+item.lower().replace(' ','-')+'.png') for item in CUSHIONS}
        self.action_art={name:photo(f'button-{name}.png') for name in ('pet','play','decorate','idle','desktop')}
        self.outfit_cache={}
        self.hand_art=photo('cursor-pet.png')
        self.toy_art={p:photo(f'toy-{DEFAULT_TOYS[p]}.png') for p in PETS}
        self.pet_icons={p:photo(f'{p.lower()}_icon.png') for p in PETS}
        self.rooms_art={r:photo(f'room-{slug}.png') for r,slug in ROOM_FILES.items()}
        self.rooms_thumb={r:photo(f'room-{slug}-thumb.png') for r,slug in ROOM_FILES.items()}
        self.items_art={n:photo(f'item-{n.lower().replace(' ', '-')}.png') for n in ITEMS+['gift','gift-open','leaves']}
        self.items_small={n:photo(f'item-{n.lower().replace(' ', '-')}-small.png') for n in ITEMS+['gift','gift-open','leaves']}
        self.currency_art={name:photo(f'currency-{name}.png') for name in ('leaves','moonstones')}
        self.gift_result=None;self.gift_reveal_at=0;self.gift_close_at=0

    def label(self,parent,text,size=11,bold=False,bg=PANEL,**kw):
        from naming import display_text
        text=display_text(self.state.data,text)
        w=tk.Label(parent,text=text,bg=bg,fg=INK,font=(self.heading_font if bold else self.body_font,size,'bold' if bold else 'normal'),**kw)
        return w

    def card(self,parent,**kw):
        return tk.Frame(parent,bg=PANEL,highlightbackground=BORDER,highlightthickness=1,**kw)

    def build(self):
        top=tk.Frame(self.root,bg=CREAM);top.pack(fill='x',padx=20,pady=(16,8))
        self.label(top,'Little ♥\nCompanions',24,True,bg=CREAM,justify='left').pack(side='left',padx=(0,30))
        self.nav={}
        for name in ('Pet Space','Collection','Rewards','Friends','Settings','Diagnostics'):
            icons={'Pet Space':'⌂','Collection':'▤','Rewards':'♧','Friends':'♡','Settings':'⚙','Diagnostics':'⋯'}
            self.nav[name]=self.button(top,icons[name]+'  '+name,lambda n=name:self.show(n))
        ornament(top)
        tk.Label(self.root,textvariable=self.banner,bg=CREAM,fg=INK,font=(self.body_font,9)).pack(anchor='w',padx=24,pady=(0,8))
        body=tk.Frame(self.root,bg=CREAM);body.pack(fill='both',expand=True,padx=20)
        body.columnconfigure(1,weight=1);body.rowconfigure(0,weight=1)
        left=self.card(body,width=224);left.grid(row=0,column=0,sticky='nsew',padx=(0,12));left.pack_propagate(False)
        heading=tk.Frame(left,bg=PANEL);heading.pack(fill='x',pady=12);ornament(heading)
        self.label(heading,'Your companions',14,True).pack(side='left')
        self.pet_buttons={}
        for p,v in PETS.items():
            b=tk.Button(left,text=f'{self.state.data["names"][p]}\n{v[0].replace(" • ",chr(10))}',image=self.pet_icons[p],compound='left',command=lambda n=p:self.select(n),bg=PANEL,fg=INK,relief='flat',font=(self.body_font,10),justify='left',anchor='w',cursor='hand2',padx=2,pady=3,highlightthickness=2,highlightbackground=BORDER)
            b.pack(fill='x',padx=8,pady=5);self.pet_buttons[p]=b
        self.label(left,'♥ 4 companions • All included',10).pack(pady=12)
        self.label(left,'Desktop mode',15,True).pack(pady=(18,5))
        self.label(left,'A little friend beside you\nwhile you work or study.',10,justify='center').pack()
        row=tk.Frame(left,bg=PANEL);row.pack(pady=12);self.button(row,'Open companion',self.desktop_mode,True)
        self.content=tk.Frame(body,bg=CREAM);self.content.grid(row=0,column=1,sticky='nsew')
        right=tk.Frame(body,bg=CREAM,width=264);right.grid(row=0,column=2,sticky='nsew',padx=(12,0));right.pack_propagate(False)
        rewards=self.card(right);rewards.pack(fill='x',pady=(0,12))
        self.label(rewards,'♧ Activity rewards',16,True).pack(anchor='w',padx=14,pady=(14,4))
        self.reward_count=self.label(rewards,'');self.reward_count.pack(anchor='w',padx=14)
        style=ttk.Style(self.root);style.theme_use('clam');style.configure('Cozy.Horizontal.TProgressbar',background='#ef997b',troughcolor='#eed7b6',bordercolor='#eed7b6',lightcolor='#ef997b',darkcolor='#ef997b')
        self.reward_progress=ttk.Progressbar(rewards,maximum=GIFT_THRESHOLD,style='Cozy.Horizontal.TProgressbar');self.reward_progress.pack(fill='x',padx=14,pady=8)
        self.label(rewards,'Free gifts for everyday activity.\nNo paid random rewards.',10,justify='left').pack(anchor='w',padx=14)
        gift=tk.Button(rewards,image=self.items_small['gift'],bg=PANEL,relief='flat',command=lambda:self.show('Rewards'),cursor='hand2');gift.pack(side='left',padx=8)
        row=tk.Frame(rewards,bg=PANEL);row.pack(side='left');self.button(row,'View rewards',lambda:self.show('Rewards'))
        rooms=self.card(right);rooms.pack(fill='x')
        self.label(rooms,'⌂ Rooms ❧',17,True).pack(anchor='w',padx=14,pady=12)
        grid=tk.Frame(rooms,bg=PANEL);grid.pack(padx=4)
        self.room_buttons={}
        for i,r in enumerate(THEMES[:4]):
            b=tk.Button(grid,image=self.rooms_thumb[r],text=r,compound='top',bg=PANEL,fg=INK,font=(self.body_font,9),relief='flat',cursor='hand2',command=lambda r=r:self.choose_room(r))
            b.grid(row=i//2,column=i%2,padx=1,pady=3);self.room_buttons[r]=b
        self.label(rooms,'Four starter rooms • Included',10).pack(pady=12)
        tk.Label(right,textvariable=self.stats,bg=CREAM,fg=INK,wraplength=245,justify='left',font=(self.body_font,10)).pack(anchor='w',pady=15,padx=5)
        tk.Label(self.root,textvariable=self.notice,bg=CREAM,fg=INK,wraplength=1250,font=(self.body_font,10)).pack(fill='x',padx=20,pady=10)
        self.show('Pet Space')

    def choose_room(self,room):
        self.change_room(room);self.show('Pet Space')

    def show(self,panel):
        if hasattr(self,'debug'):self.debug.event('Opened '+panel)
        self.panel=panel;self.canvas=None;self.gift_canvas=None
        if hasattr(self,'size_label'):del self.size_label
        for w in self.content.winfo_children():w.destroy()
        d=self.state.data;p=d['pet']
        for n,b in self.nav.items():b.configure(bg=SAGE if n==panel else '#f4e5ce')
        for n,b in self.pet_buttons.items():b.configure(bg='#fae6d5' if n==p else PANEL,highlightbackground=PEACH if n==p else BORDER)
        for r,b in self.room_buttons.items():b.configure(bg='#e2e9d7' if r==d['pet_rooms'][p] else PANEL)
        if panel=='Pet Space':self.home_panel();return
        if panel=='Diagnostics':
            from diagnostics import show_page
            show_page(self.content,self.debug);return
        if panel in ('Collection','Wardrobe','Rewards'):
            from shop_style import Banner,shop_font
            self.shop_heading_font=shop_font(self.root)
            Banner(self.content,'Little Companions • '+panel,self.shop_heading_font,title=True).pack(fill='x',pady=(4,8))
        else:self.label(self.content,panel,23,True,bg=CREAM).pack(anchor='w',pady=(8,16))
        if panel in ('Collection','Decorate'):
            self.collection_panel()
        elif panel=='Wardrobe':self.wardrobe_panel()
        elif panel=='Rewards':
            from shop_style import BotanicalCard,PAPER
            reward_card=BotanicalCard(self.content);reward_card.pack(fill='x',padx=8,pady=4)
            self.gift_canvas=tk.Canvas(reward_card.body,bg=PAPER,highlightthickness=0,height=330)
            self.gift_canvas.pack(fill='both',expand=True,pady=8)
            from comfort import gift_click
            self.gift_canvas.bind('<ButtonRelease-1>',lambda e:gift_click(self,e))
            self.gift_canvas.configure(cursor='hand2')
            self.shop_label(self.content,f"{d['gifts']} gifts ready • 250 actions earns one gift",15,True,bg=CREAM).pack(pady=8)
            self.shop_label(self.content,'Each gift gives 15 leaves + a prize.\nCommon 59% • Uncommon 25% • Rare 12% • Epic 3% • Legendary 1%\nLegendary: 40 Moonstones or two special rooms. Pajama outfits are Epic.',11,bg=CREAM,justify='center').pack(pady=4)
            self.leaf_bonus_label=self.shop_label(self.content,f"Free leaf gift: {d['leaf_bonus_progress']:,} / 1,000 clicks + keys • +200 leaves automatically",11,True,bg=CREAM);self.leaf_bonus_label.pack(pady=4)
            row=tk.Frame(self.content,bg=CREAM);row.pack(pady=12)
            b=self.shop_button(row,'Open a gift',self.open_gift,True);b.pack_configure(side='left')
            if not d['gifts']:b.configure(state='disabled')
            all_button=self.shop_button(row,'Open all',lambda:self.open_gift(True),True);all_button.pack_configure(side='left')
            if not d['gifts']:all_button.configure(state='disabled')
            self.shop_button(row,'View collection',lambda:self.show('Collection')).pack_configure(side='left')
            if getattr(self,'gift_batch',False):
                row=tk.Frame(self.content,bg=CREAM);row.pack(pady=4)
                self.shop_button(row,'‹ Previous prize',lambda:self.next_gift_prize(-1)).pack_configure(side='left');self.shop_button(row,'Next prize ›',lambda:self.next_gift_prize(1)).pack_configure(side='left');self.shop_button(row,'Done',self.close_gift_batch).pack_configure(side='left')
        elif panel=='Friends':
            self.label(self.content,'A little company, together',17,True,bg=CREAM).pack(anchor='w')
            self.label(self.content,'Private two-player rooms on your trusted local network.\nInternet and Steam invitations are coming later.',11,bg=CREAM,justify='left').pack(anchor='w',pady=12)
            row=tk.Frame(self.content,bg=CREAM);row.pack(anchor='w')
            self.button(row,'Host room',self.host);self.button(row,'Join room',self.join);self.button(row,'Leave',self.leave)
            if self.room_server:
                self.label(self.content,f'Port {self.room_server.port} • Share this invite privately:',10,bg=CREAM).pack(anchor='w',pady=12)
                token=tk.Entry(self.content,width=48);token.insert(0,self.room_token);token.configure(state='readonly');token.pack(anchor='w')
            self.friend_label=self.label(self.content,'',13,bg=CREAM,justify='left');self.friend_label.pack(anchor='w',pady=18)
            row=tk.Frame(self.content,bg=CREAM);row.pack(anchor='w');self.button(row,'Send heart ♥',lambda:self.interact('heart',count=False));self.button(row,'Wave',lambda:self.interact('wave',count=False))
        else:
            from comfort import settings_page
            settings_page(self);return

    def home_panel(self):
        d=self.state.data;p=d['pet'];room=d['pet_rooms'][p]
        head=tk.Frame(self.content,bg=CREAM);head.pack(fill='x',pady=(6,10));ornament(head)
        self.label(head,f"{d['names'][p]}'s {room} ♥",17,True,bg=CREAM).pack(side='left')
        self.button(head,'Decorate',lambda:self.show('Decorate'))
        self.canvas=tk.Canvas(self.content,bg='#f3e5d0',height=410,highlightthickness=1,highlightbackground=BORDER)
        self.canvas.pack(fill='both',expand=True);self.bind_room(self.canvas)
        row=tk.Frame(self.content,bg=CREAM);row.pack(fill='x',pady=8)
        self.interaction_toolbar(row)
        self.button(row,'Full room',self.fullscreen_room)
        edit=tk.Frame(self.content,bg=CREAM);edit.pack(fill='x')
        self.button(edit,'Smaller decoration',lambda:self.resize_decoration(-25));self.button(edit,'Larger decoration',lambda:self.resize_decoration(25))
        sizes=tk.Frame(self.content,bg=CREAM);sizes.pack(fill='x',pady=4)
        self.label(sizes,'Pet size',10,bg=CREAM).pack(side='left',padx=4)
        self.button(sizes,'−',lambda:self.set_pet_scale(self.room_scale-25))
        self.size_label=self.label(sizes,f'{self.room_scale}%',10,bg=CREAM);self.size_label.pack(side='left',padx=5)
        self.button(sizes,'+',lambda:self.set_pet_scale(self.room_scale+25))
        self.button(sizes,'Reset',lambda:self.set_pet_scale(100))
        self.label(self.content,'❧ Visit your companions',15,True,bg=CREAM).pack(anchor='w',pady=(8,6))
        visits=tk.Frame(self.content,bg=CREAM);visits.pack(fill='x')
        for pet in PETS:
            if pet==p:continue
            card=self.card(visits);card.pack(side='left',fill='x',expand=True,padx=3)
            b=tk.Button(card,text=d['names'][pet]+'  ›',image=self.pet_icons[pet],compound='left',bg=PANEL,fg=INK,relief='flat',command=lambda n=pet:self.select(n),font=(self.body_font,11,'bold'),cursor='hand2');b.pack(fill='x')
            self.label(card,d['pet_rooms'][pet],9).pack(pady=(0,6))

    def choose_collection(self,group):
        self.collection_group=group;self.show(self.panel)

    def place_reward(self,item):
        p=self.state.data['pet']
        if item in DECORATIONS:self.decorate(item)
        else:self.equip(item)
        self.show(self.panel)

    def sprite_state(self,pet,reaction=None):
        reaction=self.reaction if reaction is None else reaction
        motion={'heart':'pet','wave':'play'}.get(reaction,reaction)
        if motion not in self.motion_art[pet]:motion='idle'
        cursor=getattr(self,'cursor_reaction',None)
        if pet==self.state.data['pet'] and cursor and cursor.zone==reaction and reaction in ('pet','toy'):
            return motion,cursor.frame
        input_animation=getattr(self,'input_animations',{}).get(motion)
        if pet==self.state.data['pet'] and reaction==self.reaction and input_animation is not None:
            return motion,input_animation.frame(time.monotonic())
        if motion=='idle':
            from layered_animation import idle_index
            index=idle_index(self.art_dir,pet,time.monotonic())
        else:
            from layered_animation import timing,sequence
            count,interval=timing(self.art_dir,pet,motion)
            started=self.animation_started if reaction==self.reaction else 0
            index=int(max(0,time.monotonic()-started)/interval)%count
            if motion=='toy' and reaction==self.reaction and not sequence(self.art_dir,pet,motion):
                index=self.toy_side if index%2 else 0
        return motion,index

    def sprite(self,pet,reaction=None):
        motion,index=self.sprite_state(pet,reaction)
        return self.motion_art[pet][motion][index%len(self.motion_art[pet][motion])]

    def scaled_art(self,image,percent):
        if abs(percent-100)<.01:return image
        from png_scaling import resized_png
        width=max(1,round(image.width()*percent/100));height=max(1,round(image.height()*percent/100))
        key=(str(image),width,height)
        if key not in self.scale_cache:
            result=tk.PhotoImage(master=self.root,data=resized_png(self.art_paths[str(image)],width,height),format='png')
            self.scale_cache[key]=result
        return self.scale_cache[key]

    def rotated_art(self,image,percent,angle):
        if not angle:return self.scaled_art(image,percent)
        from png_scaling import transformed_png
        width=max(1,round(image.width()*percent/100));height=max(1,round(image.height()*percent/100))
        key=(str(image),width,height,angle)
        if key not in self.scale_cache:
            result=tk.PhotoImage(master=self.root,data=transformed_png(self.art_paths[str(image)],width,height,angle),format='png')
            self.scale_cache[key]=result
        return self.scale_cache[key]

    def selected_toy_art(self,pet):
        from model import TOY_CURSORS
        item=TOY_CURSORS.get(self.state.data.get('toy_cursor','Favorite toy'))
        return self.items_small[item] if item else self.toy_art[pet]

    def paint_pet(self,c,pet,x,floor,reaction=None,percent=None,angle=0):
        percent=self.room_scale if percent is None else percent;scale=percent/100
        motion,index=self.sprite_state(pet,reaction)
        local=pet==self.state.data['pet'] and reaction is None
        facing=self.pet_facing() if local else 0
        cushion=self.current_cushion() if local else 'Default'
        away=local and getattr(self,'wander',None) is not None
        seat=None if cushion in ('Default','None') else cushion
        if cushion=='Default' and pet=='Mochi':seat='Pumpkin Cushion'
        if away:seat=None
        center_y=floor-155*scale
        walking=local and self.walking_now()
        direction=None
        if walking:
            from layered_animation import walking_timing
            direction=self.wander['direction']
            count,interval=walking_timing(direction)
            index=int((time.monotonic()-self.wander['started'])/interval)%count
            angle=0
        path=outfit_sprite(self.art_dir,self.state.data,pet,motion,index,walking=direction,facing=facing)
        if path:
            # The approved front-facing Mochi drawings include her pink cushion.
            # Walking/turning drawings are cushion-free, with the same ground anchor.
            baked_cushion=False
            if baked_cushion:seat=None
            offset=(-43 if seat else 0)*scale
            key=str(path)
            if key not in self.outfit_cache:
                if len(self.outfit_cache)>=128:self.outfit_cache.pop(next(iter(self.outfit_cache)))
                art=tk.PhotoImage(file=key);self.art_paths[str(art)]=path;self.outfit_cache[key]=art
            art=self.outfit_cache[key]
            if 'layered-motions' in path.parts:
                offset=(155-art.height()/2)*scale
        else:
            baked_default=pet=='Mochi' and cushion=='Default' and not facing and not away
            if baked_default:seat=None
            bare=pet=='Mochi' and not baked_default
            offset=(28 if bare and not seat else (-15 if seat and pet=='Mochi' else (-43 if seat else 0)))*scale
            art=self.walk_art[pet][direction][index] if walking else self.turn_art[pet][facing] if facing else (self.mochi_bare[motion][index] if bare else self.motion_art[pet][motion][index])
            if walking:art=self.walk_art[pet][direction][index];offset=0
        if seat:c.create_image(x,center_y,image=self.scaled_art(self.seat_art[seat],percent))
        c.create_image(x,center_y+offset,image=self.rotated_art(art,percent,angle))
        if local:
            from accessory_layers import layer_paths
            base_path=getattr(self,'art_paths',{}).get(str(art))
            if base_path:
                for overlay in layer_paths(self.art_dir,self.state.data,pet,base_path):
                    key=str(overlay)
                    if key not in self.outfit_cache:
                        if len(self.outfit_cache)>=320:self.outfit_cache.pop(next(iter(self.outfit_cache)))
                        layer=tk.PhotoImage(file=key);self.art_paths[str(layer)]=overlay;self.outfit_cache[key]=layer
                    c.create_image(x,center_y+offset,image=self.rotated_art(self.outfit_cache[key],percent,angle))

        if motion=='sleep':
            phase=time.monotonic()%2/2
            for i in range(3):
                size=(5+i*3)*scale;bx=x+(60+i*22)*scale;by=center_y-(55+i*23+phase*14)*scale
                c.create_oval(bx-size,by-size,bx+size,by+size,fill='#fff8eb',outline='#bea58d',width=1)
            c.create_text(x+104*scale,center_y-(105+phase*14)*scale,text='z',fill=INK,font=(self.body_font,max(8,round(12*scale)),'bold'))

    def scene(self,c=None):
        c=c or self.canvas
        from rendering_cache import scene_key
        signature=scene_key(self,c)
        if getattr(c,'_cozy_scene_key',None)==signature:return
        c.delete('all');w=c.winfo_width();h=c.winfo_height();d=self.state.data;p=d['pet'];room=getattr(self,'previewing_room',None) or d['pet_rooms'][p]
        bg=self.rooms_art.get(room,self.rooms_art['Cozy Nook'])
        view=self.view(c)
        c.create_image(w/2,h/2,image=self.scaled_art(bg,view.scale*100))
        if getattr(self,'previewing_room',None):
            c.create_rectangle(8,8,w-8,48,fill=CREAM,outline='')
            c.create_text(w/2,28,text=room+' • Preview only',fill=INK,font=(self.heading_font,16,'bold'))
            c.create_rectangle(12,h-48,165,h-10,fill='#edb399',outline='',tags='preview_close')
            c.create_text(88,h-29,text='Back to my room',fill=INK,tags='preview_close')
            c.tag_bind('preview_close','<Button-1>',lambda e:self.close_preview())
            c.create_text(w/2,h-28,text='Select owned rooms directly in the Rooms list',fill=INK)
            c._cozy_scene_key=signature
            return
        seat_skipped=False
        for item in sorted(d['decorations'][p],key=lambda i:self.decoration_layout(i)['y']):
            if item_name(item)==self.current_cushion() and not seat_skipped:
                seat_skipped=True;continue
            v=self.decoration_layout(item)
            x,y=view.point(v['x'],v['y'])
            c.create_image(x,y-45*v['scale']/100*view.scale,image=self.rotated_art(self.items_small[item_name(item)],v['scale']*view.scale,v.get('angle',0)))
        if getattr(self,'wander',None):
            cushion=self.current_cushion()
            if cushion=='Default' and p=='Mochi':cushion='Pumpkin Cushion'
            if cushion not in ('Default','None'):
                home=self.pet_placement();hx,hy=view.point(home['x'],home['y'])
                c.create_image(hx,hy-155*self.room_scale/100*view.scale,image=self.scaled_art(self.seat_art[cushion],self.room_scale*view.scale))
        cx,floor=view.point(*self.pet_position())
        self.paint_pet(c,p,cx,floor,percent=self.room_scale*view.scale,angle=self.pet_placement()['angle'])
        if self.interaction_mode=='edit' and self.selected_decoration=='@pet':
            c.create_text(cx,floor+5,text='Pet selected • Q / E to rotate',fill=INK,anchor='n')
        if self.interaction_mode=='edit' and self.selected_decoration in d['decorations'][p]:
            bounds=self.decoration_bounds(c,self.selected_decoration)
            c.create_rectangle(*bounds,outline='#604333',width=2,dash=(5,3))
            c.create_text((bounds[0]+bounds[2])/2,bounds[1]-12,text=item_name(self.selected_decoration),fill=INK)
        if getattr(self,'hover_zone',None) in ('toy','pet') and self.pointer and self.pointer[0]==c and self.interaction_mode!='edit':
            c.create_image(self.pointer[1]+(14 if self.hover_zone=='pet' else 0),self.pointer[2]+(14 if self.hover_zone=='pet' else 0),image=self.hand_art if self.hover_zone=='pet' else self.scaled_art(self.selected_toy_art(p),self.state.data.get('cursor_scale',100)))
        if self.interaction_mode=='edit':
            c.create_text(16,52,anchor='nw',text='ARRANGE • Drag pet or items • Scroll: size • Q / E: rotate',fill=INK,font=(self.body_font,11,'bold'))
        for i,(title,command) in enumerate([('Turn ↶',lambda:self.turn_pet(-1)),('Turn ↷',lambda:self.turn_pet(1)),('Stop spin' if getattr(self,'spinning',False) else 'Spin',self.toggle_spin),('Cushion ▾',self.cushion_menu),('Arrange',lambda:self.set_interaction_mode('edit'))]):
            left=8+i*94;tag='room_control_'+str(i)
            c.create_rectangle(left,8,left+88,34,fill=CREAM,outline='#e3c8a9',tags=tag)
            c.create_text(left+44,21,text=title,fill=INK,font=(self.body_font,9,'bold'),tags=tag)
            c.tag_bind(tag,'<Button-1>',lambda e,cmd=command:(cmd(),'break')[1])
        others=[q for q in self.remote if q['id']!=self.player_id]
        if others:
            q=others[0];x,y=view.point(.80,.92);self.paint_pet(c,q['pet'],x,y,q['reaction'],percent=self.room_scale*view.scale);c.create_text(*view.point(.80,.96),text=q['name'],fill=INK)

        c._cozy_scene_key=signature

    def render_animals(self):
        if self.canvas and self.root.state() not in ('iconic','withdrawn'):self.scene()
        if self.room_canvas and self.room_canvas.winfo_exists():self.scene(self.room_canvas)
        if self.native_desktop and self.native_desktop.visible:
            try:self.native_desktop.render()
            except OSError as exc:
                self.native_desktop.hide();self.root.deiconify();self.notice.set(f'Desktop graphics error: {exc}')
                if hasattr(self,'debug'):self.debug.caught('Desktop graphics failure',exc)
        if self.desktop and self.desktop.winfo_exists() and self.desktop.state()!='withdrawn':
            for key,label in getattr(self,'desktop_balances',{}).items():label.configure(text=f" {self.state.data[key]:,}"+(" clicks" if key=="clicks" else " types" if key=="keystrokes" else ""))
            c=self.desktop_canvas;c.delete('all');self.paint_pet(c,self.state.data['pet'],c.winfo_width()/2,c.winfo_height(),percent=self.desktop_scale)
        d=self.state.data
        from rendering_cache import configure_changed
        configure_changed(self.reward_count,text=f"Next gift: {d['points']} / {GIFT_THRESHOLD} • {d['gifts']} ready")
        configure_changed(self.reward_progress,value=d['points'])
        if self.gift_canvas:
            from comfort import draw_gift
            draw_gift(self,time.monotonic())
