"""Shared in-game dialog styling; all actions remain local Tk operations."""
import tkinter as tk
from types import SimpleNamespace
from cozy_ui import CREAM,INK,CozyButton,ornament,install_fonts

def window(parent,title,size=None):
    parent=parent or tk._default_root
    win=tk.Toplevel(parent);win.title(title);win.configure(bg='#d8bea0');win.transient(parent.winfo_toplevel())
    frame=tk.Frame(win,bg=CREAM,highlightthickness=1,highlightbackground='#dfc7a6');frame.pack(fill='both',expand=True,padx=2,pady=2)
    heading,bodyfont=install_fonts(win)
    top=tk.Frame(frame,bg='#eee5ce');top.pack(fill='x');ornament(top)
    tk.Label(top,text=title,font=(heading,16,'bold'),bg='#eee5ce',fg=INK,wraplength=650,anchor='w').pack(side='left',fill='x',expand=True,padx=5,pady=10)
    CozyButton(top,'×',win.destroy,(bodyfont,12,'bold')).pack(side='right',padx=8)
    body=tk.Frame(frame,bg=CREAM);body.pack(fill='both',expand=True,padx=12,pady=10)
    win.bind('<Escape>',lambda e:win.destroy())
    if size:win.geometry(size)
    win.update_idletasks()
    root=parent.winfo_toplevel();x=max(0,root.winfo_rootx()+(root.winfo_width()-win.winfo_reqwidth())//2);y=max(0,root.winfo_rooty()+80)
    win.geometry(f'+{x}+{y}')
    return win,body

def dialog(title,message,parent=None,entry=False,initialvalue='',confirm=False,**kwargs):
    parent=parent or tk._default_root
    win,body=window(parent,title);heading,font=install_fonts(win);result=[None if entry else False]
    tk.Label(body,text=message,wraplength=470,justify='left',bg=CREAM,fg=INK,font=(font,11)).pack(fill='x',padx=8,pady=10)
    field=None
    if entry:
        field=tk.Entry(body,bg='#fffcf4',fg=INK,insertbackground=INK,relief='flat',highlightthickness=2,highlightbackground='#dfc7a6',highlightcolor='#a5b486',font=(font,12),width=38)
        field.insert(0,initialvalue or '');field.pack(fill='x',padx=8,pady=10)
    def accept():
        result[0]=field.get() if entry else True;win.destroy()
    row=tk.Frame(body,bg=CREAM);row.pack(pady=8)
    ok=CozyButton(row,'Save' if entry else 'Confirm' if confirm else 'OK',accept,(font,11,'bold'),True);ok.pack(side='left',padx=5)
    if entry or confirm:CozyButton(row,'Cancel',win.destroy,(font,11,'bold')).pack(side='left',padx=5)
    win.bind('<Return>',lambda e:accept() if not isinstance(e.widget,CozyButton) else None);win.protocol('WM_DELETE_WINDOW',win.destroy)
    previous=win.grab_current()
    win.wait_visibility();win.grab_set()
    if field:field.focus_set();field.selection_range(0,'end')
    else:ok.focus_set()
    win.wait_window()
    if previous is not None and previous.winfo_exists():previous.grab_set()
    return result[0]

def askyesno(title,message,**kwargs):return bool(dialog(title,message,confirm=True,**kwargs))
def askstring(title,prompt,**kwargs):return dialog(title,prompt,entry=True,**kwargs)
def showinfo(title,message,**kwargs):dialog(title,message,**kwargs)
messagebox=SimpleNamespace(askyesno=askyesno,showinfo=showinfo,showwarning=showinfo,showerror=showinfo)
simpledialog=SimpleNamespace(askstring=askstring)
