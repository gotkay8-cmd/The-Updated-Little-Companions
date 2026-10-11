from shop_style import Banner,BotanicalCard,ShopButton,add_to_grid,paper,scallop,shop_font,PAPER,PLUM
from model import HALLOWEEN_ITEMS,halloween_active,shop_available
from cozy_ui import CozyScrollbar,CozyChoice
"""Live room browser and companion visit cards, replacing static mockup regions."""
import tkinter as tk
from decoration_inventory import total_owned,free_count,placed_here,locations
from wardrobe import CATALOG,available,equipped
from tkinter import ttk
from cozy_dialogs import messagebox,simpledialog,window as cozy_window
from model import PETS,THEMES,ROOM_PRICES,ITEMS,ACCESSORIES,DECORATIONS,TOY_CURSORS,price_label,ITEM_RARITY,RARITY_COLORS,sale_value
from cozy_ui import rounded

CREAM='#fff8eb';INK='#604333'

def animal_groups(items):
    from model import SIGNATURE_ITEMS
    groups={pet:[] for pet in PETS};groups['Shared']=[]
    for item in items:
        pet=CATALOG.get(item,{}).get('pet') or next((p for p,owned in SIGNATURE_ITEMS.items() if item in owned),'Shared')
        groups[pet].append(item)
    return [(pet,names) for pet,names in groups.items() if names]

def swapped_visitors(visitors,previous,selected):
    result=list(visitors)
    if selected==previous:return result
    if selected in result:result[result.index(selected)]=previous
    else:result=[p for p in PETS if p!=selected]
    return result

def filter_collection_ownership(items,data,mode='All'):
    owned=set(data.get('items',[]))|set(data.get('rooms',[]))
    return [item for item in items if mode=='All' or (item in owned if mode=='Owned' else item not in owned)]

class LivePanels:
    def filter_collection_owned(self,mode):
        self.collection_ownership=mode;self.show('Collection')

    def preview_outfit(self,item):
        from outfit_preview import open_preview
        open_preview(self,item)

    def collection_panel(self):
        from decoration_inventory import collection_counts
        from model import SIGNATURE_ITEMS,SHARED_DECOR,UNIVERSAL_TOYS
        from cozy_ui import rounded
        from comfort import lifetime_panel
        lifetime_panel(self,self.content)
        self.shop_heading_font=shop_font(self.root)
        d=self.state.data;p=d['pet'];current=getattr(self,'collection_group','All')
        from cozy_ui import selection_row
        def rarity_filter(parent):
            cell=tk.Frame(parent,bg=CREAM)
            self.shop_label(cell,'Rarity',10,bg=CREAM).pack(side='left',padx=5)
            CozyChoice(cell,getattr(self,'rarity_order','Rarest first'),['Rarest first','Common first'],self.sort_collection,(self.body_font,10,'bold')).pack(side='left',padx=4,pady=4)
            self.shop_label(cell,'Ownership',10,bg=CREAM).pack(side='left',padx=5)
            CozyChoice(cell,getattr(self,'collection_ownership','All'),['All','Owned','Unowned'],self.filter_collection_owned,(self.body_font,10,'bold')).pack(side='left',padx=4,pady=4)
            return cell
        selection_row(self,self.content,[(d['names'].get(group,group),lambda g=group:self.choose_collection(g),group==current) for group in ['All']+list(PETS)+['Essentials','Rooms']]+[('Wardrobe',lambda:self.show('Wardrobe'),False),('Reward history',self.reward_history_window,False)],extra=rarity_filter)
        self.shop_label(self.content,'Image bubbles: owned copies • copies in use (rooms: companions using it)',10,bg=CREAM).pack(pady=6)
        visible=(ITEMS+THEMES if current=='All' else THEMES if current=='Rooms' else DECORATIONS[:4]+SHARED_DECOR+UNIVERSAL_TOYS if current=='Essentials' else SIGNATURE_ITEMS[current]+[i for i in ACCESSORIES if available(i,current)])
        from naming import rarity_sorted
        visible=filter_collection_ownership(visible,d,getattr(self,'collection_ownership','All'))
        visible=rarity_sorted(visible,getattr(self,'rarity_order','Rarest first'))
        shell=tk.Frame(self.content,bg=CREAM);shell.pack(fill='both',expand=True)
        canvas=tk.Canvas(shell,bg=CREAM,highlightthickness=0);scroll=CozyScrollbar(shell,command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set,yscrollincrement=36);scroll.pack(side='right',fill='y');canvas.pack(side='left',fill='both',expand=True)
        grid=tk.Frame(canvas,bg=CREAM);window=canvas.create_window(0,0,window=grid,anchor='nw')
        canvas.bind('<Configure>',lambda e:canvas.itemconfigure(window,width=e.width))
        grid.bind('<Configure>',lambda e:canvas.configure(scrollregion=canvas.bbox('all')))
        for col in range(3):grid.columnconfigure(col,weight=1,uniform='collection')
        if not visible:self.shop_label(grid,'No items match these filters.',12,bg=CREAM).grid(row=0,column=0,columnspan=3,pady=24)
        for i,item in enumerate(visible):
            outer=BotanicalCard(grid,item in HALLOWEEN_ITEMS);outer.grid(row=i//3,column=i%3,sticky='nsew',padx=4,pady=5);box=outer.body
            art=self.rooms_thumb[item] if item in THEMES else self.items_small[item]
            image=tk.Canvas(box,width=205,height=116,bg=PAPER,highlightthickness=0);image.pack()
            paper(image,205,116,item in HALLOWEEN_ITEMS)
            image.create_image(102,58,image=art)
            rounded(image,5,2,105,25,12,fill=RARITY_COLORS[ITEM_RARITY[item]],outline='#fff8eb')
            image.create_text(55,13,text=ITEM_RARITY[item],fill='white',font=(self.body_font,9,'bold'))
            owned,used=collection_counts(d,item)
            for x,label,color in [(4,f'Owned {owned}','#f4d9bd'),(108,f'In use {used}','#dce6cf')]:
                rounded(image,x,86,x+94,112,13,fill=color,outline='#cbb493')
                image.create_text(x+47,99,text=label,fill=INK,font=(self.body_font,9,'bold'))
            Banner(box,item,self.shop_heading_font,small=True).pack(fill='x')
            rarity=self.shop_label(box,ITEM_RARITY[item],10);rarity.configure(fg=RARITY_COLORS[ITEM_RARITY[item]]);rarity.pack()
            row=tk.Frame(box,bg=PAPER);row.pack(pady=5)
            if item in THEMES:
                self.shop_button(row,'View' if owned else price_label(item),lambda room=item:self.select_collection_room(room))
            else:
                self.shop_label(box,price_label(item),10).pack()
                active=bool(placed_here(d,item)) or item in equipped(d,p)
                action=(lambda name=item:self.place_reward(name)) if owned else (lambda name=item:self.item_action(name))
                button=self.shop_button(row,('Remove' if active else 'Place' if item in DECORATIONS else 'Wear') if owned else 'Buy',action,owned>0)
                if item in ACCESSORIES and not available(item,p) and owned:button.configure(state='disabled')
                if item in ACCESSORIES:self.shop_button(row,'Preview',lambda name=item:self.preview_outfit(name))
        tag='CollectionScroll'+str(id(canvas))
        def scroll_by(steps):canvas.yview_scroll(steps,'units');return 'break'
        for event,fn in [('<MouseWheel>',lambda e:scroll_by(-1 if e.delta>0 else 1)),('<Button-4>',lambda e:scroll_by(-1)),('<Button-5>',lambda e:scroll_by(1))]:self.root.bind_class(tag,event,fn)
        def bind_tree(w):
            w.bindtags((tag,)+w.bindtags())
            for child in w.winfo_children():bind_tree(child)
        bind_tree(canvas)
        canvas.bind('<Destroy>',lambda e:[self.root.unbind_class(tag,event) for event in ('<MouseWheel>','<Button-4>','<Button-5>')] if e.widget==canvas else None)

    def wardrobe_panel(self):
        from wardrobe_fitting import build_fitting_room
        build_fitting_room(self)

    def choose_wardrobe(self,pet):self.wardrobe_group=pet;self.show('Wardrobe')
    def wear_from_wardrobe(self,item,pet=None):
        self.select(pet or CATALOG[item]['pet'] or self.state.data['pet']);self.equip(item);self.save();self.show('Wardrobe')

    def sort_collection(self,order):
        self.rarity_order=order;self.show(self.panel)

    def select_collection_room(self,room):
        self.select_room_from_list(room);self.show('Pet Space')

    def build_live_panels(self):
        self.visit_pets=[p for p in PETS if p!=self.state.data['pet']]
        self.rooms_panel=tk.Frame(self.shell,bg=CREAM)
        self.room_browser=tk.Canvas(self.rooms_panel,bg=CREAM,highlightthickness=0)
        self.room_scroll=CozyScrollbar(self.rooms_panel,orient='vertical',command=self.room_browser.yview)
        self.room_browser.configure(yscrollcommand=self.room_scroll.set)
        self.room_scroll.pack(side='right',fill='y');self.room_browser.pack(side='left',fill='both',expand=True)
        self.room_browser.bind('<MouseWheel>',lambda e:self.scroll_rooms(-1 if e.delta>0 else 1))
        self.room_browser.bind('<Button-4>',lambda e:self.scroll_rooms(-1));self.room_browser.bind('<Button-5>',lambda e:self.scroll_rooms(1))
        self.visits_canvas=tk.Canvas(self.shell,bg=CREAM,highlightthickness=0)
        self.room_images=[];self.visit_images=[]

    def scroll_rooms(self,steps):self.room_browser.yview_scroll(steps,'units');return 'break'

    def position_live_panels(self):
        if not hasattr(self,'rooms_panel'):return
        if self.panel!='Pet Space':self.rooms_panel.place_forget();self.visits_canvas.place_forget();return
        s=getattr(self,'ui_scale',1);ox=getattr(self,'ui_x',0);oy=getattr(self,'ui_y',0)
        self.rooms_panel.place(x=round(ox+1195*s),y=round(oy+444*s),width=round(314*s),height=round(309*s))
        self.visits_canvas.place(x=round(ox+365*s),y=round(oy+776*s),width=round(1142*s),height=round(187*s))
        self.redraw_live_panels()

    def redraw_live_panels(self):
        if not hasattr(self,'rooms_panel') or self.panel!='Pet Space':return
        d=self.state.data
        signature=(halloween_active(),getattr(self,'ui_scale',1),d['pet'],tuple(d['rooms']),tuple(d['pet_rooms'].items()),tuple(self.visit_pets),tuple(d['names'].values()))
        if signature==getattr(self,'live_panel_signature',None):return
        self.live_panel_signature=signature
        s=getattr(self,'ui_scale',1);c=self.room_browser;position=c.yview()[0];c.delete('all');self.room_images=[]
        d=self.state.data;selected=d['pet_rooms'][d['pet']]
        width=294*s;cell=width/2;row_height=147*s
        visible_rooms=[r for r in THEMES if shop_available(r) or r in d['rooms']]
        for i,room in enumerate(visible_rooms):
            x=(i%2)*cell;y=(i//2)*row_height;tag='room'+str(i);owned=room in d['rooms'];active=room==selected
            rounded(c,x+2,y+2,x+cell-4,y+row_height-4,12*s,fill='#fffaf0',outline='#f59475' if active else '#ead7bd',width=3 if active else 1,tags=tag)
            im=self.scaled_art(self.rooms_thumb[room],(cell-14)/120*100);self.room_images.append(im)
            c.create_image(x+cell/2-1,y+7,image=im,anchor='n',tags=tag)
            c.create_text(x+cell/2,y+102*s,text=room,width=cell-10,font=(self.heading_font,max(8,round(10*s)),'bold'),fill=INK,tags=tag)
            if room in HALLOWEEN_ITEMS and halloween_active():
                rounded(c,x+8*s,y+8*s,x+cell-8*s,y+29*s,7*s,fill='#744b77',outline='#f1ca96',tags=tag)
                c.create_text(x+cell/2,y+18*s,text='Limited • until Nov 7',fill='#fff8eb',font=(self.body_font,max(7,round(8*s)),'bold'),tags=tag)
            if not owned:
                buytag='buy'+str(i)
                c.create_rectangle(x+14*s,y+116*s,x+cell-14*s,y+140*s,fill='#edb399',outline='',tags=buytag)
                c.create_text(x+cell/2,y+128*s,text=f'Buy • {price_label(room)}',font=(self.body_font,max(8,round(9*s))),fill=INK,tags=buytag)
                c.tag_bind(buytag,'<ButtonRelease-1>',lambda e,r=room:self.confirm_room_buy(r))
            if active:
                c.create_oval(x+cell-32*s,y+10*s,x+cell-9*s,y+33*s,fill='#f59475',outline='white',tags=tag)
                c.create_text(x+cell-20*s,y+21*s,text='✓',fill='white',font=(self.body_font,max(8,round(12*s)),'bold'),tags=tag)
            c.tag_bind(tag,'<ButtonRelease-1>',lambda e,r=room:self.select_room_from_list(r))
            c.tag_bind(tag,'<Enter>',lambda e:c.configure(cursor='hand2'))
        c.configure(scrollregion=(0,0,width,((len(visible_rooms)+1)//2)*row_height),yscrollincrement=max(1,round(36*s)));c.yview_moveto(position)
        self.draw_visit_cards()

    def activate_or_buy_room(self,room):
        if room in self.state.data['rooms']:return
        self.notice.set(self.state.buy(room));self.dirty=True
        self.last_dynamic=None;self.draw_reference_state();self.redraw_live_panels()
        if self.panel=='Shop':self.refresh_shop()

    def draw_visit_cards(self):
        s=getattr(self,'ui_scale',1);c=self.visits_canvas;c.delete('all');self.visit_images=[]
        for i,pet in enumerate(self.visit_pets):
            x=i*384*s;tag='visit'+str(i);room=self.state.data['pet_rooms'][pet]
            rounded(c,x+1,1,x+370*s,184*s,14*s,fill='#fff6e6',outline='#e6cfac',tags=tag)
            # Real assigned room and pet, rather than the fixed mockup visitor.
            art=self.rooms_thumb[room];bg=self.scaled_art(art,300*s);self.visit_images.append(bg)
            c.create_image(x+185*s,5*s,image=bg,anchor='n',tags=tag)
            petart=self.scaled_art(self.motion_art[pet]['idle'][0],43*s);self.visit_images.append(petart)
            c.create_image(x+185*s,151*s,image=petart,anchor='s',tags=tag)
            c.create_rectangle(x+2,153*s,x+369*s,182*s,fill='#fff6e6',outline='',tags=tag)
            c.create_text(x+12*s,168*s,text=self.state.data['names'][pet]+'  ♥',anchor='w',font=(self.heading_font,max(9,round(15*s)),'bold'),fill=INK,tags=tag)
            c.create_text(x+350*s,167*s,text='›',font=(self.heading_font,max(12,round(22*s))),fill=INK,tags=tag)
            c.tag_bind(tag,'<ButtonRelease-1>',lambda e,p=pet:self.visit_companion(p))
            c.tag_bind(tag,'<Enter>',lambda e:c.configure(cursor='hand2'))

    def visit_companion(self,pet):self.select(pet);self.show('Pet Space')

    def shop_label(self,parent,text,size=11,bold=False,bg=PAPER,**kw):
        from naming import display_text
        return tk.Label(parent,text=display_text(self.state.data,text),bg=bg,fg=INK,font=(self.shop_heading_font,size,'bold' if bold else 'normal'),**kw)

    def shop_button(self,parent,text,command,accent=False):
        button=ShopButton(parent,text,command,self.shop_heading_font,accent,seasonal=text=='Halloween')
        button.pack(side='top',fill='x',padx=4,pady=3)
        return button

    def room_shop(self):
        self.shop_heading_font=shop_font(self.root)
        Banner(self.content,'Little Companions • Cozy Shop',self.shop_heading_font,title=True).pack(fill='x',padx=6,pady=(4,0))
        header=tk.Frame(self.content,bg=CREAM);header.pack(pady=(0,8))
        self.shop_balance={}
        for key,name in [('coins','leaves'),('moonstones','moonstones')]:
            label=self.shop_label(header,'',12,True,bg=CREAM,image=self.currency_art[name],compound='left')
            label.pack(side='left',padx=8);self.shop_balance[key]=label
        self.shop_button(header,'Exchange',self.premium_wallet)
        shell=tk.Frame(self.content,bg=CREAM);shell.pack(fill='both',expand=True)
        sidebar=tk.Frame(shell,bg=CREAM,width=155);sidebar.pack(side='left',fill='y',padx=(0,8));sidebar.pack_propagate(False)
        for title in ('Exchange','Rooms','Outfits','Accessories','Décor','Toys','Halloween','Duplicates'):
            self.shop_button(sidebar,title,lambda name=title:self.shop_jump(name)).pack_configure(side='top',fill='x',pady=5)
        self.shop_canvas=c=tk.Canvas(shell,bg=CREAM,highlightthickness=0)
        scroll=CozyScrollbar(shell,command=c.yview);c.configure(yscrollcommand=scroll.set,yscrollincrement=35)
        scroll.pack(side='right',fill='y');c.pack(side='left',fill='both',expand=True)
        self.shop_body=body=tk.Frame(c,bg=CREAM);window=c.create_window(0,0,window=body,anchor='nw')
        c.bind('<Configure>',lambda e:c.itemconfigure(window,width=e.width))
        body.bind('<Configure>',lambda e:c.configure(scrollregion=c.bbox('all')))
        self.shop_scroll_tag='ShopScroll'+str(id(c))
        self.root.bind_class(self.shop_scroll_tag,'<MouseWheel>',lambda e:self.scroll_shop(-1 if e.delta>0 else 1))
        self.root.bind_class(self.shop_scroll_tag,'<Button-4>',lambda e:self.scroll_shop(-1))
        self.root.bind_class(self.shop_scroll_tag,'<Button-5>',lambda e:self.scroll_shop(1))
        tag=self.shop_scroll_tag
        c.bind('<Destroy>',lambda e:[self.root.unbind_class(tag,event) for event in ('<MouseWheel>','<Button-4>','<Button-5>')] if e.widget==c else None)
        self.refresh_shop()

    def refresh_season(self,now):
        if now<getattr(self,'next_season_check',0):return
        self.next_season_check=now+1
        active=halloween_active()
        previous=getattr(self,'last_halloween_active',active)
        self.last_halloween_active=active
        if previous==active:return
        if not active and getattr(self,'previewing_room',None) in HALLOWEEN_ITEMS and self.previewing_room not in self.state.data['rooms']:
            self.previewing_room=None
        self.live_panel_signature=None
        self.redraw_live_panels()
        if self.panel=='Shop':self.refresh_shop()

    def shop_jump(self,title):
        self.shop_body.update_idletasks()
        target=self.shop_sections[title]
        self.shop_canvas.yview_moveto(max(0,target.winfo_y()-12)/max(1,self.shop_body.winfo_height()))

    def scroll_shop(self,step):
        if getattr(self,'shop_canvas',None) and self.shop_canvas.winfo_exists():self.shop_canvas.yview_scroll(step,'units')
        return 'break'

    def refresh_shop(self):
        if not getattr(self,'shop_body',None) or not self.shop_body.winfo_exists():return
        position=self.shop_canvas.yview()[0]
        for child in self.shop_body.winfo_children():child.destroy()
        self.shop_images=[];d=self.state.data;p=d['pet']
        for key,label in self.shop_balance.items():label.configure(text=f" {d[key]:,}")
        self.shop_sections={}
        def section(title,anchor=True):
            seasonal=title=='Halloween'
            heading=Banner(self.shop_body,title,self.shop_heading_font,seasonal=seasonal,small=not anchor)
            heading.pack(fill='x',padx=12,pady=(15 if anchor else 4,3))
            if anchor:self.shop_sections['Outfits' if title.startswith('Complete outfits') else title]=heading
            grid=tk.Frame(self.shop_body,bg=CREAM);grid.pack(fill='x',padx=5)
            return grid
        def card(grid,i,name,art,count=None):
            seasonal=name in HALLOWEEN_ITEMS
            outer=BotanicalCard(grid,seasonal);add_to_grid(grid,outer);box=outer.body
            art=self.items_art.get(name,art)
            self.shop_images.append(art)
            image=tk.Canvas(box,width=210,height=190,bg=PAPER,highlightthickness=0);image.pack(pady=(0,2))
            paper(image,210,190,seasonal)
            image.create_image(105,106,image=art)
            if count is not None:
                scallop(image,7,6,48,34,'#f3bd97','#d3966d',step=10)
                image.create_text(31,23,text=str(count),fill=INK,font=(self.shop_heading_font,13,'bold'))
            if seasonal and halloween_active():
                scallop(image,140,4,64,62,PLUM,step=12)
                image.create_text(172,23,text='LIMITED\nTIME',fill='#fff8eb',font=(self.shop_heading_font,8,'bold'))
                image.create_text(172,51,text='Nov 7',fill='#fff8eb',font=(self.shop_heading_font,8))
            Banner(box,name,self.shop_heading_font,small=True).pack(fill='x',padx=0)
            if name in ITEM_RARITY:
                tier=tk.Canvas(box,width=210,height=29,bg=PAPER,highlightthickness=0);tier.pack(fill='x',padx=5)
                def draw_tier(event,n=name,c=tier):
                    c.delete('all');w=c.winfo_width()
                    scallop(c,5,4,max(1,w-10),20,'#d8dcb7',step=12)
                    c.create_text(w/2,14,text=ITEM_RARITY[n],fill=INK,font=(self.shop_heading_font,10,'bold'))
                tier.bind('<Configure>',draw_tier)
            buttons=tk.Frame(box,bg=PAPER);buttons.pack(fill='x',padx=6,pady=5)
            return buttons
        exchange_grid=section('Exchange')
        self.exchange_panel(exchange_grid)
        grid=section('Rooms')
        for i,room in enumerate(r for r in ROOM_PRICES if shop_available(r)):
            buttons=card(grid,i,room,self.rooms_thumb[room]);owned=room in d['rooms']
            self.shop_button(buttons,'Preview',lambda r=room:self.preview_room(r))
            if not owned:self.shop_button(buttons,'Buy • '+price_label(room),lambda r=room:self.confirm_room_buy(r),True)
        for title,items in [('Complete outfits • All companions',[i for i in ACCESSORIES if CATALOG[i]['slot']=='outfit']),('Accessories',[i for i in ACCESSORIES if CATALOG[i]['slot']!='outfit']),('Décor',DECORATIONS)]:
            grid=section(title)
            for animal,entries in animal_groups([item for item in items if shop_available(item)]):
                grid=section(d['names'].get(animal,animal),False)
                for i,item in enumerate(entries):
                    buttons=card(grid,i,item,self.items_small[item]);owned=item in d['items']
                    label=('Remove' if item in equipped(d,(CATALOG[item]['pet'] or d['pet'])) else 'Wear') if item in ACCESSORIES else ('Remove' if placed_here(d,item) else 'Place')
                    self.shop_button(buttons,label if owned else 'Buy • '+price_label(item),lambda name=item:self.shop_item_action(name),True)
                    if item in ACCESSORIES:
                        self.shop_button(buttons.master,'Preview animations',lambda name=item:self.preview_outfit(name)).pack_configure(side='top',fill='x',padx=6,pady=2)
                    if item in DECORATIONS and owned:
                        self.shop_label(buttons.master,f'{total_owned(d,item)} owned • {free_count(d,item)} available',10).pack(pady=3)
                        self.shop_button(buttons.master,'Buy another • '+price_label(item),lambda name=item:self.shop_buy_copy(name)).pack_configure(side='top',fill='x',padx=6,pady=2)
                        self.shop_button(buttons.master,'Add another to this room',lambda name=item:self.shop_add_copy(name)).pack_configure(side='top',fill='x',padx=6,pady=2)
    
        section('Toys')
        for animal in PETS:
            grid=section(d['names'][animal],False)
            buttons=card(grid,0,'Favorite toy',self.toy_art[animal])
            self.shop_button(buttons,'Selected' if p==animal and d['toy_cursor']=='Favorite toy' else 'Use toy',lambda pet=animal:self.shop_favorite_action(pet),True)
        grid=section('Shared toys',False)
        for i,(name,item) in enumerate((pair for pair in TOY_CURSORS.items() if pair[1] and shop_available(pair[1]))):
            buttons=card(grid,i,name,self.items_small[item]);owned=item in d['items']
            label='Selected' if d['toy_cursor']==name else ('Use toy' if owned else 'Buy • '+price_label(item))
            self.shop_button(buttons,label,lambda n=name:self.shop_cursor_action(n),True)
        grid=section('Halloween')
        seasonal=[item for item in list(ROOM_PRICES)+ACCESSORIES+DECORATIONS if item in HALLOWEEN_ITEMS and shop_available(item)]
        if not seasonal:
            self.shop_label(grid,'Halloween has ended. Your owned items are still in Collection and Wardrobe.',12,bg=CREAM,wraplength=650).grid(row=0,column=0,columnspan=3,pady=20)
        else:
            self.shop_label(grid,'Limited time • Available until November 7, 2026',11,True,bg=CREAM).grid(row=0,column=0,columnspan=3,pady=(0,8))
            for animal,entries in animal_groups(seasonal):
                grid=section(d['names'].get(animal,animal),False)
                for i,item in enumerate(entries):
                    buttons=card(grid,i,item,self.rooms_thumb[item] if item in ROOM_PRICES else self.items_small[item])
                    if item in ROOM_PRICES:
                        self.shop_button(buttons,'Preview',lambda name=item:self.preview_room(name))
                        if item not in d['rooms']:self.shop_button(buttons,'Buy • '+price_label(item),lambda name=item:self.confirm_room_buy(name),True)
                        else:self.shop_label(buttons.master,'Owned',10).pack()
                        continue
                    owned=item in d['items']
                    label=('Remove' if item in equipped(d,(CATALOG[item]['pet'] or d['pet'])) else 'Wear') if item in ACCESSORIES else ('Remove' if placed_here(d,item) else 'Place')
                    self.shop_button(buttons,label if owned else 'Buy • '+price_label(item),lambda name=item:self.shop_item_action(name),True)
                    if item in ACCESSORIES:
                        self.shop_button(buttons.master,'Preview animations',lambda name=item:self.preview_outfit(name)).pack_configure(side='top',fill='x',padx=6,pady=2)
                    if item in DECORATIONS and owned:
                        self.shop_label(buttons.master,f'{total_owned(d,item)} owned • {free_count(d,item)} available',10).pack(pady=3)
                        self.shop_button(buttons.master,'Buy another • '+price_label(item),lambda name=item:self.shop_buy_copy(name)).pack_configure(side='top',fill='x',padx=6,pady=2)
                        self.shop_button(buttons.master,'Add another to this room',lambda name=item:self.shop_add_copy(name)).pack_configure(side='top',fill='x',padx=6,pady=2)
                    if owned and item in TOY_CURSORS:
                        self.shop_button(buttons.master,'Selected toy' if d['toy_cursor']==item else 'Use toy',lambda name=item:self.shop_cursor_action(name)).pack_configure(side='top',fill='x',padx=6,pady=2)
        grid=section('Duplicates')
        groups=animal_groups(sorted(d['duplicates']))
        if not groups:self.shop_label(grid,'No duplicates yet. Extra rewards will appear here.',12,bg=CREAM).grid(row=0,column=0,columnspan=3,pady=20)
        for animal,entries in groups:
            grid=section(d['names'].get(animal,animal),False)
            for i,item in enumerate(entries):
                count=d['duplicates'][item]
                buttons=card(grid,i,item,self.items_small.get(item,self.rooms_thumb.get(item)),count)
                button=self.shop_button(buttons,f'Sell duplicate • {sale_value(item)} leaves',lambda name=item:self.shop_sell_duplicate(name),True)
                if item in DECORATIONS:
                    sellable=min(count,free_count(d,item))
                    self.shop_label(buttons.master,f'{sellable} spare copies available to sell',10).pack()
                    if not sellable:button.configure(state='disabled')
        def bind_tree(widget):
            widget.bindtags((self.shop_scroll_tag,)+tuple(t for t in widget.bindtags() if t!=self.shop_scroll_tag))
            for child in widget.winfo_children():bind_tree(child)
        bind_tree(self.shop_body);bind_tree(self.shop_canvas)
        self.shop_body.update_idletasks();self.shop_canvas.configure(scrollregion=self.shop_canvas.bbox('all'));self.shop_canvas.yview_moveto(position)

    def shop_item_action(self,item):
        if item not in self.state.data['items']:self.notice.set(self.state.buy(item))
        elif item in ACCESSORIES:
            self.select(CATALOG[item]['pet'] or self.state.data['pet']);self.equip(item)
        else:self.previewing_room=None;self.decorate(item)
        self.dirty=True;self.save();self.refresh_shop()

    def shop_buy_copy(self,item):
        self.notice.set(self.state.buy(item));self.dirty=True;self.save();self.refresh_shop()

    def shop_add_copy(self,item):
        if getattr(self,'previewing_room',None):
            self.notice.set('Return to your owned room before adding decorations.');return
        self.notice.set(self.state.place_decoration(item));self.dirty=True;self.save();self.refresh_shop()

    def shop_favorite_action(self,pet):
        self.select(pet);self.shop_cursor_action('Favorite toy')

    def shop_cursor_action(self,name):
        item=TOY_CURSORS[name]
        if item and item not in self.state.data['items']:self.notice.set(self.state.buy(item))
        if item is None or item in self.state.data['items']:self.state.data['toy_cursor']=name
        self.dirty=True;self.save();self.refresh_shop()

    def shop_sell_duplicate(self,item):
        self.notice.set(self.state.sell_duplicate(item));self.dirty=True;self.save();self.refresh_shop()

    def select_room_from_list(self,room):
        if room not in self.state.data['rooms']:self.preview_room(room);return
        self.change_room(room);self.pointer=None;self.held=False
        self.last_dynamic=None
        self.render_animals()
        self.notice.set('Room selected: '+room)

    def premium_wallet(self):
        self.show('Shop');self.shop_jump('Exchange')

    def exchange_panel(self,parent):
        box=self.card(parent);box.grid(row=0,column=0,columnspan=3,sticky='ew',padx=6,pady=6)
        self.label(box,'Moonstones ↔ Leaves',17,True).pack(anchor='w',padx=16,pady=(12,4))
        self.label(box,'1 Moonstone = 1,000 leaves • No fee',11).pack(anchor='w',padx=16)
        row=tk.Frame(box,bg='#fffcf4');row.pack(fill='x',padx=12,pady=8)
        self.label(row,'Number of Moonstones',11).pack(side='left',padx=4)
        self.exchange_amount=tk.StringVar(master=self.root,value='1')
        self.exchange_pending=None
        entry=tk.Entry(row,textvariable=self.exchange_amount,width=10,bg=CREAM,fg=INK,insertbackground=INK,relief='flat',highlightthickness=2,highlightbackground='#dfc7a6',highlightcolor='#a5b486',font=(self.body_font,12))
        entry.pack(side='left',padx=8,ipady=5)
        self.button(row,'Get leaves',lambda:self.prepare_exchange('to_leaves'))
        self.button(row,'Get Moonstones',lambda:self.prepare_exchange('to_moonstones'))
        self.exchange_preview=self.label(box,getattr(self,'exchange_message','Choose an amount and a direction to preview your exchange.'),11,True,wraplength=650,justify='left')
        self.exchange_preview.pack(anchor='w',padx=16,pady=6)
        row=tk.Frame(box,bg='#fffcf4');row.pack(anchor='w',padx=12,pady=(0,10))
        self.button(row,'Confirm exchange',self.confirm_exchange,True);self.button(row,'Cancel',self.cancel_exchange)
        self.exchange_amount.trace_add('write',lambda *_:self.cancel_exchange())

    def cancel_exchange(self):
        self.exchange_pending=None;self.exchange_message='Choose an amount and a direction to preview your exchange.'
        self.exchange_preview.configure(text=self.exchange_message)

    def prepare_exchange(self,direction):
        self.exchange_pending=None
        try:units=int(self.exchange_amount.get())
        except ValueError:units=0
        if units<1:message='Enter a positive whole number of Moonstones.'
        elif direction not in ('to_leaves','to_moonstones'):message='Choose an exchange direction.'
        elif self.state.data['moonstones' if direction=='to_leaves' else 'coins'] < units*(1 if direction=='to_leaves' else 1000):message='Not enough currency for that exchange.'
        else:
            self.exchange_pending=(direction,units)
            message=(f'{units:,} Moonstones → {units*1000:,} leaves' if direction=='to_leaves' else f'{units*1000:,} leaves → {units:,} Moonstones')+' • Confirm below.'
        self.exchange_message=message;self.exchange_preview.configure(text=message)

    def confirm_exchange(self):
        pending=getattr(self,'exchange_pending',None)
        if not pending:return
        self.exchange_pending=None
        self.exchange_message=self.state.exchange_currency(*pending)
        self.notice.set(self.exchange_message);self.dirty=True;self.save();self.refresh_shop()

    def preview_room(self,room):
        self.previewing_room=room;self.wander=None;self.stop_pointer_reaction()
        if getattr(self,'panel',None)=='Pet Space' and getattr(self,'canvas',None):self.render_animals()
        else:self.show('Pet Space')

    def close_preview(self):
        self.previewing_room=None;self.render_animals()

    def confirm_room_buy(self,room):
        if room not in self.state.data['rooms'] and not shop_available(room):
            self.notice.set('This Halloween room is no longer for sale.');return
        if room in self.state.data['rooms']:self.preview_room(room);return
        if messagebox.askyesno('Buy room',f'Buy {room} for {price_label(room)}?',parent=self.root):
            self.activate_or_buy_room(room);self.save()

    def duplicate_store(self):self.show('Shop')

    def item_shop(self):self.show('Shop')

    def owned_decoration_picker(self):
        if getattr(self,'previewing_room',None):
            self.notice.set('Return to your owned room before adding decorations.');return
        if getattr(self,'decoration_picker',None) and self.decoration_picker.winfo_exists():self.decoration_picker.lift();return
        win,dialog_body=cozy_window(self.root,'Decorate your room','730x560');self.decoration_picker=win
        heading=self.label(dialog_body,'',16,True,bg=CREAM);heading.pack(pady=10)
        shell=tk.Frame(dialog_body,bg=CREAM);shell.pack(fill='both',expand=True,padx=10,pady=8)
        c=tk.Canvas(shell,bg=CREAM,highlightthickness=0);scroll=CozyScrollbar(shell,command=c.yview);c.configure(yscrollcommand=scroll.set)
        c.pack(side='left',fill='both',expand=True);scroll.pack(side='right',fill='y')
        body=tk.Frame(c,bg=CREAM);c.create_window(0,0,window=body,anchor='nw');body.bind('<Configure>',lambda e:c.configure(scrollregion=c.bbox('all')))
        def refresh():
            for child in body.winfo_children():child.destroy()
            p=self.state.data['pet'];slots=self.state.data['decorations'][p]
            heading.configure(text=f"{self.state.data['names'][p]}'s room • {len(slots)} decorations placed")
            owned=[i for i in DECORATIONS if i in self.state.data['items']]
            if not owned:
                self.label(body,'No decorations owned yet. Open gifts or visit Shop.',12,bg=CREAM).pack(padx=16,pady=30)
            for i,item in enumerate(owned):
                card=self.card(body);card.grid(row=i//3,column=i%3,padx=8,pady=8)
                tk.Label(card,image=self.items_small[item],bg='#fffcf4').pack();self.label(card,item,11,True).pack()
                count=len(placed_here(self.state.data,item));available=free_count(self.state.data,item)
                if not count and self.current_cushion()==item:count=1
                self.label(card,f'{count} here • {available} available',10).pack()
                def change(add,name=item):
                    result=self.state.place_decoration(name) if add else self.state.remove_decoration(name)
                    self.notice.set(result);self.dirty=True;self.save();refresh();self.render_animals()
                buttons=tk.Frame(card,bg='#fffcf4');buttons.pack(pady=5)
                self.button(buttons,'Add',lambda n=item,fn=change:fn(True,n),True)
                remove=self.button(buttons,'Remove',lambda n=item,fn=change:fn(False,n))
                if not count:remove.configure(state='disabled')
                if not available:
                    self.label(card,'Used in: '+', '.join(locations(self.state.data,item)),9,wraplength=185).pack()
        refresh();self.button(dialog_body,'Close',win.destroy)

    def reward_history_window(self):
        win,body=cozy_window(self.root,'Reward history','920x540')
        self.label(body,'New gifts and duplicate sales are recorded from this update onward.',11,bg=CREAM).pack(pady=5)
        frame=tk.Frame(body,bg=CREAM);frame.pack(fill='both',expand=True,padx=12,pady=8)
        style=ttk.Style(self.root);style.theme_use('clam')
        style.configure('Cozy.Treeview',background='#fffcf4',fieldbackground='#fffcf4',foreground=INK,rowheight=38,font=(self.body_font,10),borderwidth=0)
        style.configure('Cozy.Treeview.Heading',background='#eee5ce',foreground=INK,font=(self.heading_font,11,'bold'),relief='flat')
        style.map('Cozy.Treeview',background=[('selected','#dce6cf')],foreground=[('selected',INK)])
        tree=ttk.Treeview(frame,style='Cozy.Treeview',columns=('time','action','item','result'),show='headings');scroll=CozyScrollbar(frame,command=tree.yview);tree.configure(yscrollcommand=scroll.set)
        for col,title in [('time','Received (UTC)'),('action','Action'),('item','Reward'),('result','Result')]:tree.heading(col,text=title)
        tree.column('time',width=180);tree.column('action',width=70);tree.column('item',width=190);tree.column('result',width=270)
        tree.pack(side='left',fill='both',expand=True);scroll.pack(side='right',fill='y')
        for e in reversed(self.state.data['reward_history']):
            result=f"Sold one spare • +{e.get('leaves',10)} leaves" if e['action']=='sale' else ('Duplicate kept' if e.get('duplicate') else 'New unlock')+' • +15 gift leaves'
            tree.insert('','end',values=(e.get('at',''),e['action'],__import__('naming').display_text(self.state.data,e['item']),(e.get('rarity',ITEM_RARITY.get(e['item'],''))+' • '+result)))
