"""Responsive botanical shop stationery. Native widgets retain all game actions."""
import math
import tkinter as tk
from tkinter import font as tkfont
from cozy_ui import rounded,CozyButton
PAPER='#fff3d9';INK='#603722';PEACH='#f6c4a0';SAGE='#b8bf91';PLUM='#79516e'

def shop_font(root):
    families=set(tkfont.families(root))
    return next((f for f in ('Georgia','Cambria','DejaVu Serif') if f in families),'TkDefaultFont')

def scallop(c,x,y,w,h,fill,edge=None,step=15):
    points=[]
    for ax,ay,bx,by in ((x,y,x+w,y),(x+w,y,x+w,y+h),(x+w,y+h,x,y+h),(x,y+h,x,y)):
        dx,dy=bx-ax,by-ay;length=math.hypot(dx,dy);n=max(1,round(length/step))
        for i in range(n*6):
            t=i/(n*6);wave=3*math.sin(math.pi*(i%6)/6)
            points.extend((ax+dx*t+dy/length*wave,ay+dy*t-dx/length*wave))
    return c.create_polygon(points,fill=fill,outline=edge or fill,smooth=True,splinesteps=8)

def flower(c,x,y,r=5):
    for a in range(5):
        angle=a*math.tau/5;px=x+math.cos(angle)*r;py=y+math.sin(angle)*r
        c.create_oval(px-r*.65,py-r*.65,px+r*.65,py+r*.65,fill='#f4b68b',outline='')
    c.create_oval(x-2,y-2,x+2,y+2,fill='#c69751',outline='')

def branch(c,x,y,flip=1,scale=1):
    c.create_line(x,y,x+flip*17*scale,y-36*scale,fill='#90965e',width=1.5)
    for dx,dy,side in ((3,-7,-1),(7,-15,1),(11,-24,-1),(16,-32,1)):
        px=x+flip*dx*scale;py=y+dy*scale
        c.create_polygon(px,py,px+flip*side*13*scale,py-9*scale,px+flip*side*10*scale,py+4*scale,fill='#a8ad77',smooth=True,outline='#929960')

def paper(c,w,h,seasonal=False):
    c.create_rectangle(0,0,w,h,fill=PAPER,outline='')
    # Sparse, deterministic flecks; drawn only when the surface size changes.
    for i in range(46):
        x=(i*83+17)%max(1,int(w));y=(i*47+11)%max(1,int(h))
        c.create_line(x,y,x+1,y+1,fill='#efdec0')
    branch(c,18,h-12,1,.65);branch(c,w-18,42,-1,.65)
    flower(c,22,24,4)
    if seasonal:
        for x,y in ((20,52),(w-20,h-28)):
            c.create_text(x,y,text='✦',fill='#b596ac',font=('TkDefaultFont',12))

class Banner(tk.Canvas):
    def __init__(self,parent,text,font,seasonal=False,title=False,small=False):
        self.caption=text;self.seasonal=seasonal;self.title=title;self.small=small
        self.textfont=(font,19 if title else 15 if not small else 11,'bold')
        super().__init__(parent,width=210,height=76 if title else 56 if not small else 54,bg=parent.cget('bg'),highlightthickness=0)
        self.bind('<Configure>',self.draw)
    def draw(self,event=None):
        self.delete('all');w=self.winfo_width();h=self.winfo_height()
        tw=tkfont.Font(root=self,font=self.textfont).measure(self.caption)
        bw=min(w-20,tw+(100 if self.title else 64));x=(w-bw)/2
        if not self.small:
            self.create_line(18,h/2,w-18,h/2,fill='#d4bc96',width=2,dash=(3,4))
            if w>400:branch(self,35,h-10,1,.75);branch(self,w-35,h-10,-1,.75)
        color=PEACH if self.title or self.small else PLUM if self.seasonal else SAGE
        scallop(self,x,9,bw,h-18,color,'#d4b48b')
        if self.title or self.small:
            rounded(self,x+7,14,x+bw-7,h-14,12,fill='',outline='#be8960',dash=(3,3))
        self.create_text(w/2,h/2,text=self.caption,fill='#fff8e8' if self.seasonal and not self.small else INK,font=self.textfont,width=max(30,bw-22))

class BotanicalCard(tk.Frame):
    def __init__(self,parent,seasonal=False):
        super().__init__(parent,bg=parent.cget('bg'))
        self.seasonal=seasonal
        self.canvas=tk.Canvas(self,bg=parent.cget('bg'),highlightthickness=0)
        self.canvas.place(x=0,y=0,relwidth=1,relheight=1)
        self.body=tk.Frame(self,bg=PAPER)
        self.body.pack(fill='both',expand=True,padx=11,pady=13)
        self.bind('<Configure>',self.draw)
    def draw(self,event=None):
        c=self.canvas;c.delete('all');w=self.winfo_width();h=self.winfo_height()
        edge='#c2a6b9' if self.seasonal else '#b6ba8c'
        scallop(c,4,5,max(1,w-9),max(1,h-11),edge)
        scallop(c,8,9,max(1,w-17),max(1,h-19),PAPER,step=14)

class ShopButton(CozyButton):
    def __init__(self,parent,text,command,font,accent=False,seasonal=False):
        self.seasonal=seasonal
        super().__init__(parent,text,command,(font,10,'bold'),accent)
        if seasonal:self.face=PLUM
        self.bind('<Configure>',lambda e:self.draw(),add='+')
    def draw(self):
        if not hasattr(self,'textfont'):return
        self.delete('all');w=max(self.width,self.winfo_width())
        color=PLUM if self.seasonal else '#f0b98f' if self.hover else self.face
        scallop(self,4,5,w-9,32,color,'#ba9778',step=12)
        rounded(self,9,9,w-10,33,10,fill='',outline='#d8b797' if self.seasonal else '#ba9778',dash=(2,3))
        self.create_text(w/2,21,text=self.caption,font=self.textfont,fill='#a99784' if self.disabled else '#fff6e3' if self.seasonal else INK)
        if self.focus_get()==self:self.create_line(18,34,w-18,34,fill=INK,dash=(2,2))
    def clicked(self,event):
        if 0<=event.x<max(self.width,self.winfo_width()) and 0<=event.y<43:self.invoke()

def add_to_grid(grid,widget):
    if not hasattr(grid,'shop_cards'):
        grid.shop_cards=[];grid.shop_columns=0
        def arrange(event=None):
            cols=max(1,min(5,max(1,grid.winfo_width())//250))
            if cols==grid.shop_columns and event is not None:return
            for col in range(5):grid.columnconfigure(col,weight=1 if col<cols else 0,uniform='shop' if col<cols else '',minsize=0)
            for i,card in enumerate(grid.shop_cards):card.grid(row=i//cols,column=i%cols,padx=5,pady=7,sticky='nsew')
            grid.shop_columns=cols
        grid.shop_arrange=arrange;grid.bind('<Configure>',arrange)
    grid.shop_cards.append(widget);grid.shop_arrange()
