"""Reference-art UI shell with live game regions and scale-aware click targets."""
import tkinter as tk
from cozy_ui import CozyMenu
from tkinter import ttk
from pathlib import Path
from interface import VisualUI,CREAM,INK
from live_panels import LivePanels,swapped_visitors
from cozy_ui import rounded
from model import PETS,THEMES,GIFT_THRESHOLD
from scene_geometry import RoomView

# Artwork uses a fixed 1536 x 1024 design grid. Hitboxes share its exact transform.
REGIONS={
 'home':(399,23,585,88),'collection':(586,23,772,88),'rewards':(773,23,959,88),
 'shop':(960,23,1146,88),'wardrobe':(1147,23,1333,88),'settings':(1334,23,1522,88),
 'visit':(860,116,1009,164),'decorate':(1014,116,1166,164),
 'pet':(367,655,463,706),'play':(471,655,567,706),'place_decor':(575,655,711,706),'idle':(719,655,805,706),
 'sleep':(813,655,909,706),'desktop':(917,655,1041,706),'rename':(1049,655,1161,706),'desktop_card':(17,721,335,990),
 'gift':(1212,316,1490,357),'friends':(357,733,755,775),
 'Mochi':(27,165,319,279),'Maple':(27,290,319,398),'Clover':(27,412,319,521),'Pip':(27,531,319,638),
 'visit_Maple':(367,778,735,961),'visit_Clover':(753,778,1120,961),'visit_Pip':(1138,778,1505,961),
 'room_Cozy Nook':(1197,449,1348,584),'room_Pocket Garden':(1357,449,1508,584),
 'room_Woodland':(1197,595,1348,751),'room_Seaside':(1357,595,1508,751),
}

def ui_transform(width,height):
    s=max(.01,min(width/1536,height/1024));return s,(width-1536*s)/2,(height-1024*s)/2

def ui_hit(width,height,x,y):
    s,ox,oy=ui_transform(width,height);x=(x-ox)/s;y=(y-oy)/s
    return next((name for name,(x0,y0,x1,y1) in REGIONS.items() if x0<=x<=x1 and y0<=y<=y1),None)

class ReferenceUI(LivePanels,VisualUI):
    def build(self):
        self.root.geometry('1536x1024');self.root.minsize(1152,768)
        self.shell=tk.Canvas(self.root,bg=CREAM,highlightthickness=0);self.shell.pack(fill='both',expand=True)
        path=self.art_dir/'ui-reference.png';self.skin=tk.PhotoImage(file=str(path));self.art_paths[str(self.skin)]=path
        self.shell.bind('<Configure>',self.layout_reference)
        self.shell.bind('<ButtonRelease-1>',self.reference_click)
        self.shell.bind('<Motion>',lambda e:self.shell.configure(cursor='hand2' if ui_hit(self.shell.winfo_width(),self.shell.winfo_height(),e.x,e.y) else 'arrow'))
        self.shell.bind('<Button-3>',self.reference_menu)
        self.content=tk.Frame(self.shell,bg=CREAM)
        self.nav={};self.pet_buttons={};self.room_buttons={}
        self.reward_count=tk.Label(self.root);self.reward_progress=ttk.Progressbar(self.root,maximum=GIFT_THRESHOLD)
        self.canvas=None;self.gift_canvas=None;self.reference_size=None;self.last_dynamic=None
        self.build_live_panels()
        self.show('Pet Space')

    def layout_reference(self,event=None):
        width=self.shell.winfo_width();height=self.shell.winfo_height()
        if width<10 or height<10:return
        self.ui_scale,self.ui_x,self.ui_y=ui_transform(width,height)
        self.reference_image=self.scaled_art(self.skin,self.ui_scale*100)
        self.shell.delete('skin');self.shell.create_image(width/2,height/2,image=self.reference_image,tags='skin')
        self.shell.tag_lower('skin');self.position_content();self.last_dynamic=None;self.draw_reference_state()

    def position_content(self):
        s=self.ui_scale if hasattr(self,'ui_scale') else 1;ox=getattr(self,'ui_x',0);oy=getattr(self,'ui_y',0)
        if self.panel=='Pet Space':
            self.content.place_forget()
            if self.canvas:self.canvas.place(x=round(ox+350*s),y=round(oy+167*s),width=round(819*s),height=round(476*s))
        else:self.content.place(x=round(ox+349*s),y=round(oy+111*s),width=round(1164*s),height=round(863*s))
        self.position_live_panels()

    def show(self,panel):
        if panel!='Pet Space':self.spinning=False
        if getattr(self,'canvas',None):self.canvas.destroy();self.canvas=None
        self.pointer=None;self.held=False
        # Shop uses the existing earned-leaf collection/purchase flow.
        if panel=='Shop':
            self.panel=panel;self.gift_canvas=None
            for w in self.content.winfo_children():w.destroy()
            self.room_shop();self.position_content();self.last_dynamic=None;return
        if panel=='Pet Space':
            self.panel=panel;self.gift_canvas=None
            for w in self.content.winfo_children():w.destroy()
            self.canvas=tk.Canvas(self.shell,bg=CREAM,highlightthickness=0)
            self.bind_room(self.canvas);self.canvas.bind('<Button-3>',self.reference_menu)
            self.canvas.bind('<Double-Button-1>',lambda e:self.fullscreen_room())
        else:
            VisualUI.show(self,panel)
        self.position_content();self.last_dynamic=None
        if hasattr(self,'ui_scale') and self.root.state() not in ('iconic','withdrawn'):self.draw_reference_state()

    def reference_click(self,e):
        action=ui_hit(self.shell.winfo_width(),self.shell.winfo_height(),e.x,e.y)
        self.dispatch_reference(action)

    def dispatch_reference(self,action):
        if action in PETS:self.select(action);return
        if action and action.startswith('visit_'):self.select(action[6:]);self.show('Pet Space');return
        if action and action.startswith('room_'):
            room=action[5:]
            self.select_room_from_list(room)
            return
        actions={'home':lambda:self.show('Pet Space'),'collection':lambda:self.show('Collection'),
                 'wardrobe':lambda:self.show('Wardrobe'),'rewards':lambda:self.show('Rewards'),'shop':lambda:self.show('Shop'),'settings':lambda:self.show('Settings'),
                 'visit':self.fullscreen_room,'decorate':self.arrange_reference,'pet':lambda:self.set_interaction_mode('pet'),
                 'play':self.play_menu,'place_decor':self.owned_decoration_picker,'idle':self.start_idle,
                 'sleep':self.start_sleep,'rename':self.rename,'desktop':self.desktop_mode,'desktop_card':self.desktop_mode,'gift':lambda:self.show('Rewards'),
                 'friends':lambda:self.show('Friends')}
        if action in actions:actions[action]()

    def arrange_reference(self):
        self.show('Pet Space');self.set_interaction_mode('edit');self.reference_menu()

    def popup(self,menu):
        try:menu.tk_popup(self.root.winfo_pointerx(),self.root.winfo_pointery())
        finally:menu.grab_release()

    def reference_menu(self,event=None):
        menu=CozyMenu(self.root,tearoff=False)
        for label,mode in [('Click','click'),('Pet near head','pet'),('Play below shoulders','toy'),('Arrange decorations','edit')]:menu.add_command(label=label,command=lambda m=mode:self.set_interaction_mode(m))
        menu.add_separator();menu.add_command(label='Choose decorations',command=lambda:self.show('Decorate'))
        menu.add_command(label='Smaller decoration',command=lambda:self.resize_decoration(-25));menu.add_command(label='Larger decoration',command=lambda:self.resize_decoration(25))
        menu.add_command(label='Turn pet left',command=lambda:self.turn_pet(-1));menu.add_command(label='Turn pet right',command=lambda:self.turn_pet(1))
        menu.add_command(label='Spin / stop pet',command=self.toggle_spin);menu.add_command(label='Choose cushion',command=self.cushion_menu)
        menu.add_command(label='Choose toy',command=self.play_menu)
        menu.add_command(label='Rotate selection left',command=lambda:self.rotate_selected(-15));menu.add_command(label='Rotate selection right',command=lambda:self.rotate_selected(15))
        menu.add_separator()
        for size in (50,75,100,125,150):menu.add_command(label=f'Pet size {size}%',command=lambda n=size:self.set_pet_scale(n))
        menu.add_command(label='Full room',command=self.fullscreen_room);menu.add_command(label='Diagnostics',command=lambda:self.show('Diagnostics'))
        self.popup(menu)

    def view(self,c):
        # Match the reference room's wide aspect ratio in both main and full room.
        w,h=c.winfo_width(),c.winfo_height();s=max(.01,min(w/819,h/476))
        return RoomView(s,(w-819*s)/2,(h-476*s)/2,819*s,476*s)

    def draw_page_tabs(self):
        """One shared label, icon and background treatment for every page tab."""
        c=self.shell;s=self.ui_scale;ox=self.ui_x;oy=self.ui_y
        def line(points,**kw):
            return c.create_line(*[v for x,y in points for v in (ox+x*s,oy+y*s)],fill='#79533f',width=2.1*s,capstyle='round',joinstyle='round',tags='live',**kw)
        rounded(c,ox+399*s,oy+22*s,ox+1525*s,oy+91*s,27*s,fill='#f7ecd9',outline='#e5ceb0',width=s,tags='live')
        from tkinter.font import Font
        tab_family=getattr(self,'heading_font',self.body_font)
        tab_font=Font(family=tab_family,size=max(8,round(13*s)),weight='bold')
        tabs=[('home','Pet Space'),('collection','Collection'),('rewards','Rewards'),('shop','Shop'),('wardrobe','Wardrobe'),('settings','Settings')]
        # Warm fabric-like tabs share one palette across every page.
        for key,label in tabs:
            x0,y0,x1,y1=REGIONS[key];active=self.panel==label
            # Padded cream labels, peach edging and a sage selected label.
            rounded(c,ox+(x0+4)*s,oy+(y0+8)*s,ox+(x1-4)*s,oy+(y1+1)*s,16*s,fill='#d6b797',outline='',tags='live')
            rounded(c,ox+(x0+4)*s,oy+(y0+3)*s,ox+(x1-4)*s,oy+(y1-3)*s,16*s,fill='#dce5c6' if active else '#f9e8cf',outline='#8c9c73' if active else '#cba381',width=2*s,tags='live')
            rounded(c,ox+(x0+7)*s,oy+(y0+6)*s,ox+(x1-7)*s,oy+(y1-6)*s,13*s,fill='',outline='#f5f6e3' if active else '#fff8e8',width=2*s,tags='live')
            rounded(c,ox+(x0+11)*s,oy+(y0+10)*s,ox+(x1-11)*s,oy+(y1-10)*s,10*s,fill='',outline='#a6b28e' if active else '#d9b696',width=s,dash=(max(1,round(3*s)),max(1,round(4*s))),tags='live')
            # Tiny stitched details and a paw for the selected page.
            accent='#82966a' if active else '#ce997d'
            cx=(x0+x1)/2;cy=y1-12
            for dx in (-24,17):
                c.create_line(ox+(cx+dx)*s,oy+cy*s,ox+(cx+dx+7)*s,oy+cy*s,fill=accent,width=s,capstyle='round',tags='live')
            if active:
                for dx,dy,rx,ry in ((0,2,5,3),(-6,-3,2,2.5),(0,-5,2,2.5),(6,-3,2,2.5)):
                    c.create_oval(ox+(cx+dx-rx)*s,oy+(cy+dy-ry)*s,ox+(cx+dx+rx)*s,oy+(cy+dy+ry)*s,fill=accent,outline='',tags='live')
            else:
                points=[(-6,-2),(-4,-5),(0,-2),(4,-5),(6,-2),(4,1),(0,4),(-4,1)]
                c.create_polygon(*[v for dx,dy in points for v in (ox+(cx+dx)*s,oy+(cy+dy)*s)],fill=accent,outline='',smooth=True,tags='live')
            text_width=tab_font.measure(label)/s
            x=(x0+x1-text_width-7)/2;y=(y0+y1)/2-3
            # A small biscuit-colored illustrated badge, with a soft inset edge.
            badge='#f1f2dc' if active else '#ffe0c2'
            c.create_oval(ox+(x-18)*s,oy+(y-19)*s,ox+(x+18)*s,oy+(y+18)*s,fill=badge,outline='#b6bd96' if active else '#deb491',width=s,tags='live')
            c.create_arc(ox+(x-15)*s,oy+(y-16)*s,ox+(x+15)*s,oy+(y+15)*s,start=35,extent=115,style='arc',outline='#fff8e7',width=2*s,tags='live')
            if key=='wardrobe':
                line([(x-2,y-7),(x-2,y-11),(x+2,y-14),(x+6,y-10),(x+2,y-4),(x+2,y)])
                line([(x+2,y),(x-11,y+9),(x+15,y+9),(x+2,y)])
            elif key=='shop':
                line([(x-10,y-6),(x+11,y-6),(x+13,y+14),(x-12,y+14),(x-10,y-6)])
                line([(x-5,y-3),(x-5,y-12),(x,y-17),(x+6,y-12),(x+6,y-3)])
            elif key=='collection':
                line([(x,y-10),(x-12,y-14),(x-12,y+11),(x,y+15),(x+12,y+11),(x+12,y-14),(x,y-10),(x,y+15)])
            elif key=='rewards':
                line([(x-12,y-5),(x+12,y-5),(x+12,y+14),(x-12,y+14),(x-12,y-5),(x+12,y-5)])
                line([(x,y+14),(x,y-6),(x-8,y-15),(x-12,y-11),(x,y-6),(x+8,y-15),(x+12,y-11),(x,y-6)])
            elif key=='home':
                line([(x-14,y-2),(x,y-15),(x+14,y-2),(x+10,y-2),(x+10,y+14),(x+3,y+14),(x+3,y+5),(x-3,y+5),(x-3,y+14),(x-10,y+14),(x-10,y-2)])
            else:
                import math
                for i in range(6):
                    dx=8*math.cos(i*math.tau/6);dy=8*math.sin(i*math.tau/6)
                    c.create_oval(ox+(x+dx-5)*s,oy+(y+dy-5)*s,ox+(x+dx+5)*s,oy+(y+dy+5)*s,fill='#99836a',outline='',tags='live')
                c.create_oval(ox+(x-4)*s,oy+(y-4)*s,ox+(x+4)*s,oy+(y+4)*s,fill=CREAM,outline='',tags='live')
            c.create_text(ox+(x+24)*s,oy+y*s,text=label,anchor='w',fill=INK,font=(tab_family,max(8,round(13*s)),'bold'),tags='live')

    def draw_reference_state(self):
        d=self.state.data;p=d['pet'];room=d['pet_rooms'][p]
        signature=(self.panel,p,room,d['points'],d['gifts'],d['coins'],d['moonstones'],tuple(d['rooms']),tuple(d['names'].values()),tuple(getattr(self,'visit_pets',[])),getattr(self,'interaction_mode','click'),self.notice.get())
        if signature==self.last_dynamic:return
        self.last_dynamic=signature;c=self.shell;c.delete('live');s=self.ui_scale;ox=self.ui_x;oy=self.ui_y
        def rect(x0,y0,x1,y1,color):c.create_rectangle(ox+x0*s,oy+y0*s,ox+x1*s,oy+y1*s,fill=color,outline='',tags='live')
        def text(x,y,value,size=14,bold=False,anchor='w'):
            c.create_text(ox+x*s,oy+y*s,text=value,anchor=anchor,fill=INK,font=(self.heading_font if bold else self.body_font,max(8,round(size*s)),'bold' if bold else 'normal'),tags='live')
        c.create_text(ox+355*s,oy+995*s,text=__import__('naming').display_text(d,self.notice.get()),anchor='w',fill=INK,font=(self.body_font,max(8,round(9*s))),width=820*s,tags='live')
        for pet in PETS:
            _,top,_,_=REGIONS[pet]
            rect(151,top+15,277,top+50,'#fff8eb')
            name=d['names'][pet]
            text(155,top+33,name,min(17,max(8,160/max(1,len(name)))),True)
        self.draw_page_tabs()
        # Static reference lettering remains untouched except genuinely dynamic values.
        rect(1209,177,1415,216,'#fcf3e2');text(1216,197,f"Next gift: {d['points']} / {GIFT_THRESHOLD}",14)
        rect(1215,222,1419,244,'#edd3b0')
        amount=204*d['points']/GIFT_THRESHOLD
        if amount:rect(1215,222,1215+amount,244,'#f28e70')
        if d['gifts']:text(1475,300,f"{d['gifts']} ready",10,anchor='e')
        if p!='Mochi' or room!='Cozy Nook' or d['names'][p]!='Mochi':
            rect(411,114,846,163,'#fff8eb');text(417,140,f"{d['names'][p]}'s {room}",min(21,max(10,520/max(1,len(d['names'][p])+len(room)))),True)
        if p!='Mochi':
            rounded(c,ox+26*s,oy+165*s,ox+320*s,oy+278*s,18*s,fill='',outline='#fff1df',width=5*s,tags='live')
            x0,y0,x1,y1=REGIONS[p];rounded(c,ox+x0*s,oy+y0*s,ox+x1*s,oy+y1*s,17*s,fill='',outline='#fb9776',width=3*s,tags='live')
        # Hide the baked-in paw, then draw it beside the currently selected pet.
        rect(276,179,310,213,'#fff0dd')
        _,y0,_,_=REGIONS[p];px=294;py=y0+28
        c.create_oval(ox+(px-8)*s,oy+(py-2)*s,ox+(px+7)*s,oy+(py+11)*s,fill='#eca37f',outline='',tags='live')
        for dx,dy in ((-10,-7),(-3,-12),(5,-11),(11,-5)):
            c.create_oval(ox+(px+dx-3)*s,oy+(py+dy-4)*s,ox+(px+dx+3)*s,oy+(py+dy+4)*s,fill='#eca37f',outline='',tags='live')
        self.currency_images=[]
        rect(1367,398,1507,441,CREAM)
        for key,name,y in [('coins','leaves',409),('moonstones','moonstones',430)]:
            im=self.scaled_art(self.currency_art[name],s*65);self.currency_images.append(im)
            c.create_image(ox+1380*s,oy+y*s,image=im,tags='live')
            text(1395,y,f"{d[key]:,}",11,True)
        self.redraw_live_panels()
        # One live action row keeps all seven controls beside one another.
        rect(354,647,1169,718,CREAM)
        self.action_images=[]
        for key,label in [('pet','Pet'),('play','Play'),('place_decor','Decorate'),('idle','Idle'),('sleep','Sleep'),('desktop','Desktop'),('rename','Rename')]:
            x0,y0,x1,y1=REGIONS[key]
            active=(key=='pet' and self.interaction_mode=='pet') or (key=='play' and self.interaction_mode=='toy')
            rounded(c,ox+x0*s,oy+(y0+3)*s,ox+x1*s,oy+(y1+3)*s,16*s,fill='#dcc6aa',outline='',tags='live')
            rounded(c,ox+x0*s,oy+y0*s,ox+x1*s,oy+y1*s,16*s,fill='#e4ead7' if active else '#f5e1c7',outline='#c9ad88',width=max(1,2*s),tags='live')
            rounded(c,ox+(x0+5)*s,oy+(y0+5)*s,ox+(x1-5)*s,oy+(y1-5)*s,12*s,fill='',outline='#fff8eb',width=max(1,s),tags='live')
            text((x0+x1)/2,(y0+y1)/2,label,17,True,anchor='center')
        if self.interaction_mode in ('pet','toy','edit'):
            positions={'pet':(377,701,453,701),'toy':(481,701,557,701),'edit':(1029,157,1150,157)}
            x0,y0,x1,y1=positions[self.interaction_mode];c.create_line(ox+x0*s,oy+y0*s,ox+x1*s,oy+y1*s,fill='#7d8b59',width=2,tags='live')
        # Selected secondary page indicator; main tab art stays in the reference style.
        key={'Collection':'collection','Decorate':'collection','Rewards':'rewards','Settings':'settings','Diagnostics':'settings'}.get(self.panel)
        if key:
            x0,y0,x1,y1=REGIONS[key];c.create_line(ox+(x0+22)*s,oy+(y1-7)*s,ox+(x1-22)*s,oy+(y1-7)*s,fill='#7d8b59',width=3,tags='live')

    def render_animals(self):
        VisualUI.render_animals(self)
        if hasattr(self,'ui_scale') and self.root.state() not in ('iconic','withdrawn'):self.draw_reference_state()
