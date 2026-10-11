from cozy_ui import CozyScrollbar,CozyToggle,CozySlider
"""Saved comfort settings and a time-based gift reveal using existing artwork."""
import math
import tkinter as tk
from tkinter import messagebox
from model import RARITY_COLORS

def gift_pose(elapsed,reveal_after,reduced=False):
    progress=max(0,min(1,(elapsed-reveal_after)/.65))
    ease=1-(1-progress)**3
    shake=0 if reduced or elapsed>=reveal_after else math.sin(elapsed*34)*5*math.sin(math.pi*max(0,elapsed)/reveal_after)
    return shake,1 if reduced else ease

def draw_gift(app,now):
    c=app.gift_canvas;c.delete('all');w=c.winfo_width();h=c.winfo_height()
    result=app.gift_result;reduced=app.state.data['view_settings'].get('reduced_effects',False)
    start=getattr(app,'gift_started',app.gift_reveal_at-.9);elapsed=max(0,now-start)
    reveal=bool(result and now>=app.gift_reveal_at)
    shake,ease=gift_pose(elapsed,max(.01,app.gift_reveal_at-start),reduced)
    x=w/2+shake;y=h*.76
    color=RARITY_COLORS.get(result.get('rarity') if result else '', '#d8bd8e')
    if result and not reduced:
        for i in range(12):
            angle=i*math.tau/12+elapsed*.22;radius=58+(70*ease if reveal else 7*math.sin(elapsed*4))
            sx=x+math.cos(angle)*radius;sy=y-35+math.sin(angle)*radius*.6
            size=(3+2*math.sin(elapsed*5+i))*(1 if getattr(app,'gift_batch',False) else min(1,max(0,(app.gift_close_at-now)/.5)))
            c.create_oval(sx-size,sy-size,sx+size,sy+size,fill=color,outline='')
    c.create_image(x,y,image=app.items_art['gift-open' if reveal else 'gift'],tags='gift-box')
    if reveal:
        item=result['item'];art=app.currency_art['moonstones'] if item=='40 Moonstones' else app.items_small.get(item,getattr(app,'rooms_thumb',{}).get(item,app.items_small['leaves']))
        c.create_image(w/2,h*.24+15*(1-ease),image=art)
        c.create_text(w/2,h*.40,text=result.get('rarity',''),fill=color,font=(app.heading_font,16,'bold'))
        from naming import display_text
        item=display_text(app.state.data,item)
        title=('Duplicate '+item+' kept' if result['duplicate'] else item+' received')+' • +15 leaves'
    else:title='Opening your surprise…' if result else 'A little surprise for you' if app.state.data['gifts'] else 'Your next gift is growing'
    if reveal and getattr(app,'gift_batch',False):
        c.create_text(w/2,h*.08,text=f"Prize {app.gift_index+1} / {len(app.gift_results)} • use arrows to browse",fill='#604333',font=(app.heading_font,11,'bold'))
        for direction,px,step in [('‹',w*.18,-1),('›',w*.82,1)]:
            from cozy_ui import rounded
            tag='prize-'+str(step);rounded(c,px-27,h*.25-25,px+27,h*.25+25,17,fill='#e5edda',outline='#a5b486',width=2,tags=tag)
            c.create_text(px,h*.25,text=direction,fill='#604333',font=(app.heading_font,30,'bold'),tags=tag)
    c.create_text(w/2,h*.47,text=title,fill='#604333',font=(app.heading_font,14,'bold'),width=max(100,w-40))

def settings_extras(app):
    frame=tk.Frame(app.content,bg='#fff8eb');frame.pack(anchor='w',fill='x',pady=5)
    app.comfort_vars={}
    choices=[('reduced_effects','Gentle gift reveal (no shaking or sparkles)',False),
             ('room_roaming','Allow idle walking in rooms',True),
             ('taskbar_running','Run along the taskbar (Windows)',True),
             ('auto_desktop','Show desktop pet when minimized',True),
             ('low_power','Lower animation rate to save power',False)]
    def update(key,var):
        app.state.data['view_settings'][key]=var.get();app.dirty=True
        if key=='room_roaming' and not var.get():app.wander=None
        app.save()
    for i,(key,label,default) in enumerate(choices):
        var=tk.BooleanVar(master=app.root,value=app.state.data['view_settings'].get(key,default));app.comfort_vars[key]=var
        CozyToggle(frame,label,var,lambda k=key,v=var:update(k,v),(app.body_font,10,'bold')).grid(row=i,column=0,sticky='w',padx=5,pady=3)

def settings_page(app):
    from tkinter import ttk
    cream='#fff8eb'
    shell=tk.Frame(app.content,bg=cream);shell.pack(fill='both',expand=True)
    canvas=tk.Canvas(shell,bg=cream,highlightthickness=0);scroll=CozyScrollbar(shell,command=canvas.yview)
    canvas.configure(yscrollcommand=scroll.set,yscrollincrement=30);scroll.pack(side='right',fill='y');canvas.pack(side='left',fill='both',expand=True)
    body=tk.Frame(canvas,bg=cream);window=canvas.create_window(0,0,window=body,anchor='nw')
    canvas.bind('<Configure>',lambda e:canvas.itemconfigure(window,width=e.width));body.bind('<Configure>',lambda e:canvas.configure(scrollregion=canvas.bbox('all')))
    original=app.content;app.content=body
    try:
        app.pause_var=tk.BooleanVar(value=app.paused);app.global_var=tk.BooleanVar(value=app.global_input)
        for label,var,command in [('Pause activity rewards',app.pause_var,app.toggle_pause),('Background clicks and typing (Windows)',app.global_var,app.toggle_global)]:
            CozyToggle(body,label,var,command,(app.body_font,10,'bold')).pack(anchor='w',pady=3)
        lifetime_panel(app,body)
        settings_extras(app)
        def size_change(value,kind):
            if kind=='toy':app.set_cursor_scale(value)
            else:app.set_pet_scale(value,desktop=kind=='desktop')
            app.save()
        for title,value,values,kind in [('Room pet size',app.room_scale,(50,75,100,125,150),'room'),('Desktop pet size',app.desktop_scale,(50,75,100,125,150),'desktop'),('Toy size',app.state.data['cursor_scale'],(50,75,100,125,150,175,200),'toy')]:
            CozySlider(body,title,value,values,lambda v,k=kind:size_change(v,k),(app.body_font,11,'bold')).pack(fill='x',padx=8,pady=5)
        app.label(body,'Keys & controls',19,True,bg=cream).pack(anchor='w',pady=12)
        for title,lines in [('Your room','F11 / double-click room — full room\nEsc / F11 in full room — return\nHover head — pet • Hover shoulders — play'),('Arrange & decorate','Drag selected objects — move • Q / E — rotate\nMouse wheel — resize • Turn controls — face another direction\nDecorate — add/remove copies • Play — toy and toy size'),('Desktop companion','Drag pet, counters or portals — move group • Mouse wheel — resize group\nRight-click — running, sleep and wake controls • Portals — hide / return'),('Collect & shop','Click gift box — open one • Open all — reveal every saved gift\nPrize arrows — browse batch loot • Collection — sort and history\nRename — 30 leaves • Exchange — 1 Moonstone = 1,000 leaves')]:
            card=app.card(body);card.pack(fill='x',padx=8,pady=5)
            app.label(card,title,13,True).pack(anchor='w',padx=12,pady=5)
            app.label(card,lines,10,justify='left',wraplength=720).pack(anchor='w',padx=12,pady=(0,8))
        row=tk.Frame(body,bg=cream);row.pack(pady=8)
        app.button(row,'Save now',app.save);app.button(row,'Currency exchange',app.premium_wallet);app.button(row,'Diagnostics',lambda:app.show('Diagnostics'))
    finally:app.content=original
    tag='SettingsScroll'+str(id(canvas))
    app.root.bind_class(tag,'<MouseWheel>',lambda e:canvas.yview_scroll(-1 if e.delta>0 else 1,'units'))
    def bind(w):
        w.bindtags((tag,)+w.bindtags())
        for child in w.winfo_children():bind(child)
    bind(canvas)
    canvas.bind('<Destroy>',lambda e:app.root.unbind_class(tag,'<MouseWheel>') if e.widget==canvas else None)


def lifetime_panel(app,parent):
    frame=tk.Frame(parent,bg='#e5edda');frame.pack(fill='x',padx=8,pady=7)
    app.label(frame,'Lifetime activity',13,True,bg='#e5edda').pack(side='left',padx=10,pady=8)
    labels=[]
    for key,title in [('clicks','Clicks'),('keystrokes','Keys typed')]:
        label=app.label(frame,f'{title}: {app.state.data[key]:,}',11,True,bg='#e5edda')
        label.pack(side='left',padx=12);labels.append((key,title,label))
    app.lifetime_labels=labels

def update_lifetime(app):
    from rendering_cache import configure_changed
    label=getattr(app,'leaf_bonus_label',None)
    if label is not None and label.winfo_exists():configure_changed(label,text=f"Free leaf gift: {app.state.data['leaf_bonus_progress']:,} / 1,000 clicks + keys • +200 leaves automatically")
    for key,title,label in getattr(app,'lifetime_labels',[]):
        if label.winfo_exists():configure_changed(label,text=f'{title}: {app.state.data[key]:,}')


def gift_click(app,event):
    """Coordinate hit tests survive the animated Canvas deleting/recreating items."""
    import time
    now=time.monotonic();c=app.gift_canvas;w=c.winfo_width();h=c.winfo_height()
    if getattr(app,'gift_batch',False) and now>=app.gift_reveal_at:
        for x,step in ((w*.18,-1),(w*.82,1)):
            if abs(event.x-x)<=27 and abs(event.y-h*.25)<=25:
                app.next_gift_prize(step);return
    if abs(event.x-w/2)<=75 and abs(event.y-h*.76)<=75:app.open_gift()
