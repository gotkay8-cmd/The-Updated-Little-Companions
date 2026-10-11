"""Local crash reports; no keystrokes, screenshots, save contents or network tokens."""
import atexit
from collections import deque
from datetime import datetime, timezone
import faulthandler
import json
import os
from pathlib import Path
import platform
import re
import sys
import threading
import traceback
import uuid

VERSION='0.47'

class Diagnostics:
    def __init__(self,directory=None):
        base=Path(os.getenv('LOCALAPPDATA',str(Path.home()/'.local/share')))/'LittleCompanions'
        self.directory=Path(directory) if directory else base/'diagnostics'
        self.directory.mkdir(parents=True,exist_ok=True)
        self.session=uuid.uuid4().hex[:12]
        self.marker=self.directory/f'session-{self.session}.json'
        self.previous=list(self.directory.glob('session-*.json'))
        self.events=deque(maxlen=40);self.lock=threading.RLock();self.provider=lambda:{}
        self.native=None;self.last_error='';self.count=0
        self.marker.write_text(json.dumps({'started':self.now(),'version':VERSION,'pid':os.getpid()}))
        self.event('Game session started')
        self.native_path=self.directory/f'native-{self.session}.txt'
        self.native=self.native_path.open('w',encoding='utf-8')
        self.native.write(f'Little Companions {VERSION} native fault log\n');self.native.flush()
        try:faulthandler.enable(self.native,all_threads=True)
        except (RuntimeError,OSError):pass
        # Keep a bounded history, including native fault files from prior launches.
        for pattern in ('error-*.txt','native-*.txt'):
            for p in sorted(self.directory.glob(pattern),key=lambda p:p.stat().st_mtime,reverse=True)[20:]:
                try:p.unlink()
                except OSError:pass
        atexit.register(self.close)

    @staticmethod
    def now():return datetime.now(timezone.utc).isoformat(timespec='seconds')

    def redact(self,text):
        text=str(text).replace(str(Path.home()),'<HOME>')
        text=re.sub(r'(?i)(token|password|secret)([\s\"\x27:=]+)[^\s,}\]]+',r'\1\2<REDACTED>',text)
        return text

    def event(self,label):
        with self.lock:self.events.append(f'{self.now()} {label}')

    def snapshot(self):
        try:state=self.provider()
        except Exception:state={'status':'Game state unavailable'}
        return {'game_version':VERSION,'python':platform.python_version(),'platform':platform.system(),
                'platform_release':platform.release(),'architecture':platform.machine(),'session':self.session,
                'prior_unclosed_sessions':len(self.previous),'game':state}

    def report(self,kind,exc_type,exc,tb):
        with self.lock:
            self.count+=1;self.last_error=f'{kind}: {exc_type.__name__}'
            content=self.redact('Little Companions error report\n'+json.dumps(self.snapshot(),indent=2)+'\n\n'+kind+'\n'+''.join(traceback.format_exception(exc_type,exc,tb))+'\nRecent actions:\n'+'\n'.join(self.events))
            path=self.directory/f'error-{datetime.now().strftime("%Y%m%d-%H%M%S-%f")}.txt'
            try:path.write_text(content,encoding='utf-8')
            except OSError:traceback.print_exception(exc_type,exc,tb)
            self.event(self.last_error)
            return path

    def caught(self,kind,exc):return self.report(kind,type(exc),exc,exc.__traceback__)

    def install(self):
        original=sys.excepthook
        def hook(t,e,tb):
            self.report('Uncaught exception',t,e,tb);original(t,e,tb)
        sys.excepthook=hook
        original_thread=threading.excepthook
        def thread_hook(args):
            self.report('Worker thread exception',args.exc_type,args.exc_value,args.exc_traceback);original_thread(args)
        threading.excepthook=thread_hook

    def attach(self,app):
        def snapshot():
            return {k:getattr(app,k,None) for k in ('panel','reaction','interaction_mode','desktop_interaction','room_scale','desktop_scale','global_input','hooked','paused')} | {'pet':app.state.data['pet'],'room':app.state.data['pet_rooms'][app.state.data['pet']]}
        self.provider=snapshot
        def callback(t,e,tb):
            self.report('Interface callback exception',t,e,tb)
            app.notice.set('An error was saved. Open Diagnostics to export the report; restart if an animation has stopped.')
            # A failing timer is not restarted automatically: avoid a repeating crash loop.
        app.root.report_callback_exception=callback
        app.debug=self
        if self.previous:app.notice.set('An earlier session did not close cleanly (or another game is open). Diagnostics has details.')

    def report_text(self):
        lines=['LITTLE COMPANIONS DIAGNOSTIC REPORT',json.dumps(self.snapshot(),indent=2),
               'Reports are local. No typed text, screenshots, invite tokens, or saved progression are collected.',
               'An unclosed session can mean a crash, force-close, power loss, or another running instance.',
               '\nRECENT ACTIONS','\n'.join(self.events)]
        for p in sorted(self.directory.glob('error-*.txt'),reverse=True)[:5]:
            lines.extend(['\n--- '+p.name+' ---',p.read_text(encoding='utf-8',errors='replace')])
        for p in sorted(self.directory.glob('native-*.txt'),key=lambda p:p.stat().st_mtime,reverse=True)[:5]:
            lines.extend(['\n--- '+p.name+' ---',p.read_text(encoding='utf-8',errors='replace')[-60000:]])
        return self.redact('\n'.join(lines))

    def close(self):
        if self.native is None:return
        try:faulthandler.disable();self.native.close()
        finally:
            self.native=None
            try:self.marker.unlink(missing_ok=True)
            except OSError:pass


def show_page(parent,debug):
    import tkinter as tk
    from cozy_dialogs import messagebox,simpledialog
    from cozy_ui import CozyButton,install_fonts
    heading,bodyfont=install_fonts(parent)
    for widget in parent.winfo_children():widget.destroy()
    tk.Label(parent,text='Diagnostics',font=(heading,22,'bold'),bg='#fff8eb',fg='#604333').pack(anchor='w',pady=12)
    tk.Label(parent,text='Errors are saved automatically on this computer. Export a report and attach it in our chat.\nNothing is sent automatically. If the game will not open, run Debug-Windows.bat.',
             justify='left',wraplength=620,bg='#fff8eb',fg='#604333').pack(anchor='w',pady=6)
    row=tk.Frame(parent,bg='#fff8eb');row.pack(fill='x')
    box=tk.Text(parent,wrap='word',height=16,font=('Consolas',10),bg='#fffcf4',fg='#604333',relief='flat',highlightthickness=1,highlightbackground='#dfc7a6');box.pack(fill='both',expand=True,pady=10)
    def refresh():
        box.configure(state='normal');box.delete('1.0','end');box.insert('1.0',debug.report_text());box.configure(state='disabled')
    def export():
        folder=Path.home()/'Desktop'
        if not folder.is_dir():folder=Path.home()
        name=simpledialog.askstring('Save diagnostic report','Choose the full file path for your report:',parent=parent,initialvalue=str(folder/'Little-Companions-Diagnostics.txt'))
        if name and Path(name).exists() and not messagebox.askyesno('Replace report','A file already exists at that path. Replace it?',parent=parent):return
        if name:
            try:Path(name).write_text(debug.report_text(),encoding='utf-8');messagebox.showinfo('Report saved','Attach this text file in our chat so we can investigate.',parent=parent)
            except OSError as exc:messagebox.showerror('Could not export',str(exc),parent=parent)
    def test():
        try:raise RuntimeError('Intentional diagnostic test — the game did not crash.')
        except RuntimeError as exc:debug.caught('User-requested test report',exc)
        refresh()
    for title,action in [('Refresh',refresh),('Export report',export),('Create test report',test)]:
        CozyButton(row,title,action,(bodyfont,10,'bold')).pack(side='left',padx=4,pady=6)
    refresh()

if __name__=='__main__':
    import tkinter as tk
    debug=Diagnostics();debug.install();root=tk.Tk();root.title('Little Companions • Diagnostics');root.geometry('880x620');root.configure(bg='#fff8eb')
    show_page(root,debug);root.mainloop();debug.close()
