"""Code-drawn rounded controls and botanical details inspired by the approved UI."""
import tkinter as tk
from tkinter import font as tkfont

CREAM='#fff8eb';INK='#604333';SAGE='#a5b486';PEACH='#f4ddbd'

def selection_positions(widths, available, gap=6):
    """Keep selections on one row when they fit; wrap only at the edge."""
    row=column=used=0;positions=[]
    for width in widths:
        if column and used+width+gap>available:
            row+=1;column=used=0
        positions.append((row,column));column+=1;used+=width+gap
    return positions

def selection_row(app,parent,choices,extra=None):
    row=tk.Frame(parent,bg=parent.cget('bg'));row.pack(fill='x',padx=4,pady=3)
    cells=[]
    for text,command,active in choices:
        cell=tk.Frame(row,bg=parent.cget('bg'))
        app.button(cell,text,command,active);cells.append(cell)
    if extra:cells.append(extra(row))
    def arrange(event=None):
        widths=[cell.winfo_reqwidth() for cell in cells]
        height=max((cell.winfo_reqheight() for cell in cells),default=0)+4
        positions=selection_positions(widths,max(1,row.winfo_width()))
        x=0
        for cell,width,(r,c) in zip(cells,widths,positions):
            if c==0:x=0
            cell.place(x=x+3,y=r*height+2,width=width,height=height-4)
            x+=width+6
        row.configure(height=(positions[-1][0]+1)*height if positions else 0)
    row.bind('<Configure>',arrange);row.after_idle(arrange)
    return row

def install_fonts(root):
    families=set(tkfont.families(root))
    heading=next((n for n in ('Comic Sans MS','Chalkboard SE','Segoe Print','DejaVu Sans') if n in families),'TkDefaultFont')
    body=next((n for n in ('Segoe Print','Comic Sans MS','Chalkboard','DejaVu Sans') if n in families),'TkDefaultFont')
    return heading,body

def rounded(c,x0,y0,x1,y1,r,**kw):
    return c.create_polygon(x0+r,y0,x1-r,y0,x1,y0,x1,y0+r,x1,y1-r,x1,y1,x1-r,y1,x0+r,y1,x0,y1,x0,y1-r,x0,y0+r,x0,y0,smooth=True,splinesteps=24,**kw)

def sprig(c,x,y,size=1):
    c.create_line(x,y+23*size,x+7*size,y-7*size,fill='#909b6d',width=2)
    for dx,dy,flip in ((0,9,-1),(4,0,1),(7,-10,1)):
        c.create_polygon(x+dx*size,y+dy*size,x+(dx+flip*13)*size,y+(dy-13)*size,x+(dx+flip*11)*size,y+(dy+3)*size,fill='#9da873',smooth=True)

def ornament(parent):
    c=tk.Canvas(parent,width=34,height=38,bg=parent.cget('bg'),highlightthickness=0)
    sprig(c,13,15,.8);c.pack(side='left',padx=(4,7));return c

class CozyButton(tk.Canvas):
    def __init__(self,parent,text,command,font,accent=False):
        self.caption=text;self.command=command;self.face=SAGE if accent else PEACH
        self.textfont=tkfont.Font(root=parent,font=font);self.disabled=False;self.hover=False
        self.width=max(45,self.textfont.measure(text)+30)
        super().__init__(parent,width=self.width,height=43,bg=parent.cget('bg'),highlightthickness=0,cursor='hand2',takefocus=True)
        self.bind('<Enter>',lambda e:self.enter(True));self.bind('<Leave>',lambda e:self.enter(False))
        self.bind('<ButtonRelease-1>',self.clicked);self.bind('<Return>',lambda e:self.invoke());self.bind('<space>',lambda e:self.invoke())
        self.bind('<FocusIn>',lambda e:self.draw());self.bind('<FocusOut>',lambda e:self.draw())
        self.draw()
    def enter(self,value):self.hover=value;self.draw()
    def clicked(self,e):
        if 0<=e.x<self.width and 0<=e.y<43:self.invoke()
    def invoke(self):
        if not self.disabled:self.command()
    def configure(self,cnf=None,**kw):
        if cnf:kw.update(cnf)
        if 'bg' in kw:self.face=kw.pop('bg')
        if 'state' in kw:self.disabled=kw.pop('state')=='disabled'
        if kw:super().configure(**kw)
        if hasattr(self,'textfont'):self.draw()
    config=configure
    def draw(self):
        self.delete('all')
        color='#e8bda0' if self.hover and not self.disabled else self.face
        rounded(self,2,3,self.width-2,41,18,fill='#dfccb1',outline='')
        rounded(self,2,1,self.width-2,38,18,fill=color,outline='#b8c391' if color==SAGE else '#e5bf9b',width=2)
        self.create_text(self.width/2,20,text=self.caption,font=self.textfont,fill='#a99784' if self.disabled else INK)
        if self.focus_get()==self:self.create_line(17,34,self.width-17,34,fill=INK,dash=(2,2))

class CozyMenu:
    """Small illustrated dropdown with scrolling, keyboard navigation and submenus."""
    def __init__(self,parent,tearoff=False):
        self.root=parent.root if isinstance(parent,CozyMenu) else parent
        self.entries=[];self.window=None;self.stack=[];self.active=0
    def add_command(self,label,command):self.entries.append((label,command,None))
    def add_separator(self):self.entries.append(None)
    def add_cascade(self,label,menu):self.entries.append((label,None,menu))
    def grab_release(self):pass # The popup owns its grab until selection/dismissal.
    def close(self):
        if self.window:
            self.window.grab_release();self.window.destroy();self.window=None
    def tk_popup(self,x,y):
        previous=getattr(self.root,'_cozy_popup',None)
        if previous:previous.close()
        self.root._cozy_popup=self
        self.window=w=tk.Toplevel(self.root);w.overrideredirect(True);w.attributes('-topmost',True)
        w.configure(bg='#d6bfa0');self.font=(install_fonts(self.root)[0],11,'bold')
        self.canvas=c=tk.Canvas(w,bg=CREAM,highlightthickness=0,width=285)
        c.pack(padx=2,pady=2,fill='both',expand=True)
        c.bind('<Motion>',self.hover);c.bind('<ButtonRelease-1>',self.select)
        c.bind('<MouseWheel>',lambda e:c.yview_scroll(-1 if e.delta>0 else 1,'units'))
        c.bind('<Button-4>',lambda e:c.yview_scroll(-1,'units'));c.bind('<Button-5>',lambda e:c.yview_scroll(1,'units'))
        w.bind('<Escape>',lambda e:self.close());w.bind('<Down>',lambda e:self.move(1));w.bind('<Up>',lambda e:self.move(-1))
        w.bind('<Return>',lambda e:self.invoke(self.active));w.bind('<Left>',lambda e:self.back())
        w.bind('<ButtonPress-1>',self.outside)
        self.draw();w.update_idletasks()
        width=w.winfo_reqwidth();height=w.winfo_reqheight()
        w.geometry(f'+{max(0,min(x,w.winfo_screenwidth()-width))}+{max(0,min(y,w.winfo_screenheight()-height))}')
        w.grab_set();w.focus_force()
    def outside(self,e):
        w=self.window
        if w and not(w.winfo_rootx()<=e.x_root<w.winfo_rootx()+w.winfo_width() and w.winfo_rooty()<=e.y_root<w.winfo_rooty()+w.winfo_height()):self.close()
    def draw(self):
        c=self.canvas;c.delete('all');y=5;self.rows=[]
        for i,entry in enumerate(self.entries):
            if entry is None:c.create_line(16,y+4,269,y+4,fill='#ead8bd');y+=10;continue
            self.rows.append((y,y+32,i))
            rounded(c,5,y,280,y+31,9,fill='#e5edda' if i==self.active else '#f9ecd8',outline='#e5d3b8')
            label,_,submenu=entry
            c.create_text(16,y+16,text=label,anchor='w',fill=INK,font=self.font)
            if submenu:c.create_text(265,y+16,text='›',fill=INK,font=self.font)
            y+=34
        c.configure(height=min(y+5,self.root.winfo_screenheight()-80),scrollregion=(0,0,285,y+5),yscrollincrement=34)
    def index_at(self,e):
        y=self.canvas.canvasy(e.y)
        return next((i for top,bottom,i in self.rows if top<=y<bottom),None)
    def hover(self,e):
        i=self.index_at(e)
        if i is not None and i!=self.active:self.active=i;self.draw()
    def select(self,e):
        i=self.index_at(e)
        if i is not None:self.invoke(i)
    def move(self,direction):
        choices=[i for i,e in enumerate(self.entries) if e]
        if not choices:return
        self.active=choices[(choices.index(self.active)+direction)%len(choices)] if self.active in choices else choices[0]
        self.draw();self.canvas.yview_moveto(max(0,self.active*34-100)/max(1,float(self.canvas.cget('scrollregion').split()[-1])))
    def back(self):
        if self.stack:self.entries=self.stack.pop();self.active=0;self.draw();self.canvas.yview_moveto(0)
        else:self.close()
    def invoke(self,i):
        entry=self.entries[i]
        if not entry:return
        _,command,submenu=entry
        if submenu:
            self.stack.append(self.entries);self.entries=[('‹ Back',self.back,None),None]+submenu.entries
            self.active=0;self.draw();self.canvas.yview_moveto(0)
        elif command==self.back:self.back()
        else:self.close();command()


def scroll_geometry(height,first,last):
    track=max(1,height-8);span=max(0,min(1,last-first))
    length=min(track,max(28,track*span));travel=track-length
    top=4+(travel*first/(1-span) if span<1 else 0)
    return top,top+length,travel

class CozyScrollbar(tk.Canvas):
    """Cream track, sage thumb; native Canvas scrolling contract."""
    def __init__(self,parent,command,orient='vertical',**kw):
        self.command=command;self.first=0.;self.last=1.;self.offset=None
        super().__init__(parent,width=18,highlightthickness=0,bg=CREAM,takefocus=True,**kw)
        self.bind('<Configure>',lambda e:self.draw())
        self.bind('<Button-1>',self.press);self.bind('<B1-Motion>',self.drag)
        self.bind('<ButtonRelease-1>',lambda e:setattr(self,'offset',None))
        self.bind('<MouseWheel>',lambda e:self.command('scroll',-1 if e.delta>0 else 1,'units'))
        self.bind('<Button-4>',lambda e:self.command('scroll',-1,'units'));self.bind('<Button-5>',lambda e:self.command('scroll',1,'units'))
        for event,direction,units in [('<Up>',-1,'units'),('<Down>',1,'units'),('<Prior>',-1,'pages'),('<Next>',1,'pages')]:
            self.bind(event,lambda e,d=direction,u=units:self.command('scroll',d,u))
        self.bind('<Home>',lambda e:self.command('moveto',0));self.bind('<End>',lambda e:self.command('moveto',1))
    def set(self,first,last):
        self.first=float(first);self.last=float(last);self.draw()
    def draw(self):
        self.delete('all');h=self.winfo_height()
        rounded(self,3,3,15,max(4,h-3),6,fill='#f3e4cc',outline='#dfc7a6')
        top,bottom,_=scroll_geometry(h,self.first,self.last)
        rounded(self,4,top,14,bottom,5,fill=SAGE,outline='#819763')
        mid=(top+bottom)/2
        for y in (mid-3,mid+3):self.create_line(7,y,11,y,fill=CREAM,width=2)
    def press(self,e):
        self.focus_set();top,bottom,_=scroll_geometry(self.winfo_height(),self.first,self.last)
        if top<=e.y<=bottom:self.offset=e.y-top
        else:self.command('scroll',-1 if e.y<top else 1,'pages')
    def drag(self,e):
        if self.offset is None:return
        _,_,travel=scroll_geometry(self.winfo_height(),self.first,self.last)
        if travel:self.command('moveto',max(0,min(1,(e.y-4-self.offset)/travel))*(1-(self.last-self.first)))


class CozyToggle(CozyButton):
    def __init__(self,parent,text,variable,command,font):
        self.variable=variable;self.label_text=text;self.changed=command
        super().__init__(parent,('On  •  ' if variable.get() else 'Off  •  ')+text,self.toggle,font,variable.get())
    def toggle(self):
        self.variable.set(not self.variable.get())
        self.caption=('On  •  ' if self.variable.get() else 'Off  •  ')+self.label_text
        self.face=SAGE if self.variable.get() else PEACH;self.draw();self.changed()

class CozyChoice(CozyButton):
    def __init__(self,parent,value,values,command,font):
        self.values=values;self.changed=command
        super().__init__(parent,value+'  ▾',self.open,font)
    def open(self):
        menu=CozyMenu(self.winfo_toplevel())
        for value in self.values:menu.add_command(label=value,command=lambda v=value:self.changed(v))
        menu.tk_popup(self.winfo_rootx(),self.winfo_rooty()+43)

class CozySlider(tk.Canvas):
    def __init__(self,parent,title,value,values,command,font):
        self.title=title;self.value=value;self.values=list(values);self.command=command;self.font=font
        super().__init__(parent,width=360,height=83,bg=parent.cget('bg'),highlightthickness=0,takefocus=True,cursor='hand2')
        self.bind('<Configure>',lambda e:self.draw());self.bind('<Button-1>',self.choose);self.bind('<B1-Motion>',self.choose)
        for event,step in [('<Left>',-1),('<Right>',1)]:self.bind(event,lambda e,s=step:self.set(self.values[max(0,min(len(self.values)-1,self.values.index(self.value)+s))]))
        self.bind('<Home>',lambda e:self.set(self.values[0]));self.bind('<End>',lambda e:self.set(self.values[-1]));self.draw()
    def set(self,value):
        if value!=self.value:self.value=value;self.draw();self.command(value)
    def choose(self,e):
        self.focus_set();span=max(1,self.winfo_width()-52)
        self.set(self.values[round(max(0,min(1,(e.x-26)/span))*(len(self.values)-1))])
    def draw(self):
        self.delete('all');w=max(360,self.winfo_width());x=26+(w-52)*self.values.index(self.value)/(len(self.values)-1)
        rounded(self,2,2,w-2,80,18,fill='#fffaf1',outline='#dfc7a6')
        self.create_text(20,22,text=self.title,anchor='w',fill=INK,font=self.font)
        self.create_text(w-20,22,text=f'{self.value}%',anchor='e',fill=INK,font=self.font)
        rounded(self,26,51,w-26,61,5,fill=PEACH,outline='#d8be9b')
        if x>26:rounded(self,26,51,x,61,5,fill=SAGE,outline='')
        self.create_oval(x-11,46,x+11,68,fill=SAGE,outline='#819763',width=2)
        self.create_oval(x-4,54,x+4,61,fill=CREAM,outline='')
        for dx,dy in [(-5,50),(0,48),(5,50)]:self.create_oval(x+dx-2,dy,x+dx+2,dy+4,fill=CREAM,outline='')
