"""Windows per-pixel-alpha companion. No color key, frame, or focus stealing.

Uses built-in Windows GDI+ to load and scale RGBA PNGs into a premultiplied
ARGB surface, then UpdateLayeredWindow to composite directly onto the desktop.
"""
import ctypes as C
from ctypes import wintypes as W
import sys
import queue
from scene_geometry import pet_zone
from model import TOY_CURSORS,DEFAULT_TOYS
from wardrobe import equipped,outfit_sprite
from taskbar_run import TaskbarRun,running_sprite
import time

CONTROL_ITEMS={
    'Mochi':('yarn-basket','crescent-cushion'),
    'Maple':('bone-basket','paw-blanket'),
    'Clover':('carrot-planter','daisy-cushion'),
    'Pip':('treasure-chest','acorn-lantern'),
}
SCALES=(50,75,100,125,150)

def clamp_scale(value):
    return min(SCALES,key=lambda n:abs(n-float(value)))

SIDE=40

SPRITE_BOUNDS={'Mochi': (46, 313), 'Maple': (52, 307), 'Clover': (44, 315), 'Pip': (57, 301)}

def layout(percent,pet="Mochi"):
    scale=clamp_scale(percent)/100
    pet_width=round(360*scale);height=round(360*scale)
    width=pet_width+SIDE*2;size=round(36*scale);gap=round(4*scale);y=max(0,round(height*.80)-size//2)
    left,right=SPRITE_BOUNDS[pet]
    return width,height,[(SIDE+round(left*scale)-size-gap,y,size,size),(SIDE+round(right*scale)+gap,y,size,size)]

def docked_position(work,width,scale,x):
    left,top,right,bottom=work
    return max(left,min(x,max(left,right-width))),bottom-round(331*scale)

def portal_at(percent,x,y,pet="Mochi"):
    for i,(bx,by,bw,bh) in enumerate(layout(percent,pet)[2]):
        if bx<=x<bx+bw and by<=y<by+bh:return i
    return None

def compact_currency(value):
    value=max(0,int(value))
    if value<1000:return str(value)
    for divisor,suffix in ((1_000_000_000,'B'),(1_000_000,'M'),(1000,'K')):
        if value>=divisor:
            n=value/divisor
            return (f'{n:.1f}'.rstrip('0').rstrip('.') if n<100 else str(int(n)))+suffix

class DesktopOverlay:
    def __init__(self,app):
        if sys.platform!='win32':raise OSError('Transparent desktop mode requires Windows.')
        self.actions=queue.SimpleQueue();self.errors=queue.SimpleQueue();self.portal_press=None
        self.app=app;self.visible=False;self.images={};self.last_signature=None
        self.hwnd=None;self.dc=None;self.bitmap=None;self.old_bitmap=None
        self.graphics=C.c_void_p();self.surface=C.c_void_p();self.drag_origin=None
        self.hud=None;self.x=80;self.y=80;self.moved=False;self.runner=TaskbarRun()
        self._api()
        self.token=C.c_size_t()
        class Startup(C.Structure):
            _fields_=[('version',W.UINT),('callback',C.c_void_p),('thread',W.BOOL),('codecs',W.BOOL)]
        startup=Startup(1,None,False,False)
        self.check(self.g.GdiplusStartup(C.byref(self.token),C.byref(startup),None))
        self.callback=self.WNDPROC(self._safe_wndproc)
        wc=self.WNDCLASS();wc.lpfnWndProc=self.callback;wc.hInstance=self.instance
        self.class_name='LittleCompanionsAlpha'+str(id(self));wc.lpszClassName=self.class_name
        if not self.u.RegisterClassW(C.byref(wc)):raise C.WinError(C.get_last_error())
        # LAYERED | TOOLWINDOW | TOPMOST | NOACTIVATE. Transparent pixels pass through.
        self.hwnd=self.u.CreateWindowExW(0x08080088,self.class_name,'Little Companions',0x80000000,self.x,self.y,360,370,None,None,self.instance,None)
        if not self.hwnd:raise C.WinError(C.get_last_error())

    def _api(self):
        self.u=C.WinDLL('user32',use_last_error=True);self.gdi=C.WinDLL('gdi32',use_last_error=True);self.g=C.WinDLL('gdiplus');k=C.WinDLL('kernel32')
        def bind(dll,name,result,args):
            f=getattr(dll,name);f.restype=result;f.argtypes=args;return f
        ptr=C.c_void_p;integer=C.c_int
        self.WNDPROC=C.WINFUNCTYPE(C.c_ssize_t,W.HWND,W.UINT,W.WPARAM,W.LPARAM)
        class WC(C.Structure):
            _fields_=[('style',W.UINT),('lpfnWndProc',self.WNDPROC),('cbClsExtra',integer),('cbWndExtra',integer),('hInstance',W.HINSTANCE),('hIcon',W.HICON),('hCursor',W.HANDLE),('hbrBackground',W.HBRUSH),('lpszMenuName',W.LPCWSTR),('lpszClassName',W.LPCWSTR)]
        self.WNDCLASS=WC
        class MonitorInfo(C.Structure):
            _fields_=[('cbSize',W.DWORD),('rcMonitor',W.RECT),('rcWork',W.RECT),('dwFlags',W.DWORD)]
        self.MONITORINFO=MonitorInfo
        bind(self.u,'MonitorFromWindow',W.HANDLE,[W.HWND,W.DWORD])
        bind(self.u,'GetMonitorInfoW',W.BOOL,[W.HANDLE,C.POINTER(MonitorInfo)])
        self.instance=bind(k,'GetModuleHandleW',W.HMODULE,[W.LPCWSTR])(None)
        bind(self.u,'RegisterClassW',W.ATOM,[C.POINTER(WC)])
        bind(self.u,'UnregisterClassW',W.BOOL,[W.LPCWSTR,W.HINSTANCE])
        bind(self.u,'CreateWindowExW',W.HWND,[W.DWORD,W.LPCWSTR,W.LPCWSTR,W.DWORD,integer,integer,integer,integer,W.HWND,W.HMENU,W.HINSTANCE,ptr])
        bind(self.u,'DefWindowProcW',C.c_ssize_t,[W.HWND,W.UINT,W.WPARAM,W.LPARAM])
        bind(self.u,'ShowWindow',W.BOOL,[W.HWND,integer]);bind(self.u,'DestroyWindow',W.BOOL,[W.HWND])
        bind(self.u,'GetCursorPos',W.BOOL,[C.POINTER(W.POINT)])
        bind(self.u,'LoadCursorW',W.HANDLE,[W.HINSTANCE,C.c_void_p])
        bind(self.u,'SetCursor',W.HANDLE,[W.HANDLE])
        bind(self.u,'SetWindowPos',W.BOOL,[W.HWND,W.HWND,integer,integer,integer,integer,W.UINT])
        bind(self.u,'SetCapture',W.HWND,[W.HWND]);bind(self.u,'ReleaseCapture',W.BOOL,[])
        bind(self.u,'UpdateLayeredWindow',W.BOOL,[W.HWND,W.HDC,C.POINTER(W.POINT),C.POINTER(W.SIZE),W.HDC,C.POINTER(W.POINT),W.DWORD,ptr,W.DWORD])
        bind(self.gdi,'CreateCompatibleDC',W.HDC,[W.HDC]);bind(self.gdi,'DeleteDC',W.BOOL,[W.HDC])
        bind(self.gdi,'CreateDIBSection',W.HBITMAP,[W.HDC,ptr,W.UINT,C.POINTER(ptr),W.HANDLE,W.DWORD])
        bind(self.gdi,'SelectObject',W.HGDIOBJ,[W.HDC,W.HGDIOBJ]);bind(self.gdi,'DeleteObject',W.BOOL,[W.HGDIOBJ])
        bind(self.g,'GdiplusStartup',integer,[C.POINTER(C.c_size_t),ptr,ptr]);bind(self.g,'GdiplusShutdown',None,[C.c_size_t])
        bind(self.g,'GdipCreateBitmapFromFile',integer,[W.LPCWSTR,C.POINTER(ptr)])
        bind(self.g,'GdipCreateBitmapFromScan0',integer,[integer,integer,integer,integer,ptr,C.POINTER(ptr)])
        bind(self.g,'GdipGetImageGraphicsContext',integer,[ptr,C.POINTER(ptr)])
        bind(self.g,'GdipGraphicsClear',integer,[ptr,W.DWORD])
        bind(self.g,'GdipSetInterpolationMode',integer,[ptr,integer])
        bind(self.g,'GdipDrawImageRectI',integer,[ptr,ptr,integer,integer,integer,integer])
        bind(self.g,'GdipCreateSolidFill',integer,[W.DWORD,C.POINTER(ptr)])
        bind(self.g,'GdipFillEllipseI',integer,[ptr,ptr,integer,integer,integer,integer])
        bind(self.g,'GdipDeleteBrush',integer,[ptr])
        bind(self.g,'GdipFlush',integer,[ptr,integer])
        bind(self.g,'GdipDeleteGraphics',integer,[ptr]);bind(self.g,'GdipDisposeImage',integer,[ptr])

    @staticmethod
    def check(status):
        if status:raise OSError('Windows graphics error '+str(status))

    def _release_surface(self):
        if self.graphics.value:self.g.GdipDeleteGraphics(self.graphics);self.graphics=C.c_void_p()
        if self.surface.value:self.g.GdipDisposeImage(self.surface);self.surface=C.c_void_p()
        if self.dc:
            if self.old_bitmap:self.gdi.SelectObject(self.dc,self.old_bitmap)
            if self.bitmap:self.gdi.DeleteObject(self.bitmap)
            self.gdi.DeleteDC(self.dc)
        self.dc=self.bitmap=self.old_bitmap=None

    def _resize(self,width,height):
        # Preserve the pet's bottom-center on screen when the scale changes.
        if hasattr(self,'width'):
            self.x+=round((self.width-width)/2);self.y+=self.height-height
        self.width=width;self.height=height;self._release_surface()
        class Header(C.Structure):
            _fields_=[('size',W.DWORD),('width',W.LONG),('height',W.LONG),('planes',W.WORD),('bits',W.WORD),('compression',W.DWORD),('imageSize',W.DWORD),('xppm',W.LONG),('yppm',W.LONG),('used',W.DWORD),('important',W.DWORD)]
        header=Header(C.sizeof(Header),width,-height,1,32,0,width*height*4,0,0,0,0)
        self.dc=self.gdi.CreateCompatibleDC(None);pixels=C.c_void_p()
        self.bitmap=self.gdi.CreateDIBSection(self.dc,C.byref(header),0,C.byref(pixels),None,0)
        if not self.dc or not self.bitmap:raise C.WinError(C.get_last_error())
        self.old_bitmap=self.gdi.SelectObject(self.dc,self.bitmap)
        # 0xE200B = PixelFormat32bppPARGB; premultiplied alpha for Windows blending.
        self.check(self.g.GdipCreateBitmapFromScan0(width,height,width*4,0xE200B,pixels,C.byref(self.surface)))
        self.check(self.g.GdipGetImageGraphicsContext(self.surface,C.byref(self.graphics)))
        self.check(self.g.GdipSetInterpolationMode(self.graphics,7))

    def _draw_image(self,path,rect):
        key=str(path.resolve())
        if key not in self.images:
            if len(self.images)>=400:
                self.g.GdipFlush(self.graphics,1)
                oldest=next(iter(self.images));self.g.GdipDisposeImage(self.images.pop(oldest))
            im=C.c_void_p();self.check(self.g.GdipCreateBitmapFromFile(key,C.byref(im)));self.images[key]=im
        self.check(self.g.GdipDrawImageRectI(self.graphics,self.images[key],*rect))

    def _dock(self):
        info=self.MONITORINFO();info.cbSize=C.sizeof(info)
        monitor=self.u.MonitorFromWindow(self.hwnd,2)
        if self.u.GetMonitorInfoW(monitor,C.byref(info)):
            r=info.rcWork
            self.work_area=(r.left,r.top,r.right,r.bottom)
            self.x,self.y=docked_position((r.left,r.top,r.right,r.bottom),self.width,self.app.desktop_scale/100,self.x)

    def portal_hit(self,x,y):
        return None

    def render(self):
        if not self.visible:return
        if getattr(self,'hud',None):self.hud.render()
        a=self.app;pet=a.state.data['pet']
        width,height,self.controls=layout(a.desktop_scale,pet)
        if not self.dc or (self.width,self.height)!=(width,height):self._resize(width,height)
        self._dock()
        point=W.POINT();self.u.GetCursorPos(C.byref(point));pointer=(point.x-self.x,point.y-self.y)
        mode=getattr(a,'desktop_interaction','click')
        w,h,_=layout(a.desktop_scale,pet);scale=a.desktop_scale/100
        zone=pet_zone(pet,(pointer[0]-SIDE)/scale,pointer[1]/scale-50)
        inside=SIDE<=pointer[0]<w-SIDE and 0<=pointer[1]<h
        mode=zone if not self.drag_origin and self.portal_hit(*pointer) is None else None
        if mode in ('toy','pet'):
            a.cursor_reaction.update(mode,(pointer[0]-SIDE)/scale,time.monotonic())
            a.toy_side=1 if pointer[0]<w/2 else 3;a.start_reaction(mode)
        else:a.stop_pointer_reaction()
        self.last_pointer=pointer
        motion,index=a.sprite_state(pet)
        now=time.monotonic()
        nearby=-18<=pointer[0]<=width+18 and -18<=pointer[1]<=height+18
        blocked=(now<getattr(self,'group_adjust_until',0) or bool(getattr(getattr(self,'hud',None),'drag_origin',None)) or not a.state.data['view_settings'].get('taskbar_running',True) or getattr(a,'manual_sleep',False) or self.drag_origin is not None or nearby or getattr(getattr(a.root,'_cozy_popup',None),'window',None) is not None or now-a.last_activity<3)
        returning=((self.runner.active or self.runner.napping) and blocked or getattr(self,'return_home_requested',False) or getattr(self,'docked_to_hud',False) and blocked) and not self.drag_origin
        work=getattr(self,'work_area',(self.x,0,self.x+width,height));home_x=None
        if getattr(self,'hud',None):
            home_x=self.hud.x+home_offset(a.desktop_scale,pet,a.state.data)
            if returning:
                work=getattr(self.hud,'work_area',work);self.work_area=work;self.y=self.hud.y
        self.x,direction,run_index=self.runner.advance(now,self.x,width,work,scale,blocked,return_home=returning,home_x=home_x)
        if returning:self.docked_to_hud=True
        elif self.runner.active or self.moved:self.docked_to_hud=False
        self.return_home_requested=False
        running=self.runner.active
        from layered_animation import timing
        if running:
            count,interval=timing(a.art_dir,pet,running=direction)
            motion,index='run',int(self.runner.phase/10/interval)%count
        elif self.runner.napping:
            count,interval=timing(a.art_dir,pet,'sleep')
            motion,index='sleep',int(now/interval)%count
        percent=a.desktop_scale;item=tuple(equipped(a.state.data,pet))
        signature=(pet,motion,index,direction if running else None,percent,item,mode,a.state.data['coins'],a.state.data['moonstones'],a.state.data['clicks'],a.state.data['keystrokes'],a.state.data.get('toy_cursor','Favorite toy'),a.state.data.get('cursor_scale',100),int(time.monotonic()*4) if motion=='sleep' else 0,self.x,self.y,pointer if mode in ('pet','toy') and inside else None)
        if signature==self.last_signature:return
        self.check(self.g.GdipGraphicsClear(self.graphics,0))
        scale=percent/100;ph=round(310*scale)
        path=running_sprite(a.art_dir,a.state.data,pet,direction,index) if running else outfit_sprite(a.art_dir,a.state.data,pet,motion,index)
        top=round(50*scale)
        if path and 'layered-motions' in path.parts:
            from layered_animation import sequence
            info=sequence(a.art_dir,pet,motion,running=direction if running else None)
            ph=round(info['size'][1]*scale)
            # The same contact baseline is used for every pose in a sequence.
            # Airborne running frames retain their lift above this baseline.
            ground=info.get('desktop_ground_y',330)
            top=round(331*scale)-round((ground+1)*scale)
        if path:
            self._draw_image(path,(SIDE,top,round(360*scale),ph))
        else:
            self._draw_image(a.art_dir/f'{pet.lower()}_{motion}_{index}.png',(SIDE,top,round(360*scale),ph))
        from accessory_layers import layer_paths
        base_path=path or a.art_dir/f'{pet.lower()}_{motion}_{index}.png'
        for overlay in layer_paths(a.art_dir,a.state.data,pet,base_path):
            self._draw_image(overlay,(SIDE,top,round(360*scale),ph))
        if mode=='toy' and inside:
            toy=TOY_CURSORS.get(a.state.data.get('toy_cursor','Favorite toy'))
            path=a.art_dir/('item-'+toy.lower().replace(' ','-')+'-small.png' if toy else f'toy-{DEFAULT_TOYS[pet]}.png')
            size=round(56*a.state.data.get('cursor_scale',100)/100)
            self._draw_image(path,(pointer[0]-size//2,pointer[1]-size//2,size,size))
        if motion=='sleep':
            brush=C.c_void_p();self.check(self.g.GdipCreateSolidFill(0xDDFFF8EB,C.byref(brush)))
            try:
                phase=time.monotonic()%2/2
                for i in range(3):
                    size=round((9+i*5)*scale)
                    self.check(self.g.GdipFillEllipseI(self.graphics,brush,SIDE+round((240+i*22)*scale),round((92-i*24-phase*12)*scale),size,size))
            finally:self.g.GdipDeleteBrush(brush)
        if mode=='pet' and inside:self._draw_image(a.art_dir/'cursor-pet.png',(pointer[0]-12,pointer[1]-12,52,52))
        self.check(self.g.GdipFlush(self.graphics,1))
        self.present(width,height)
        self.last_signature=signature

    def present(self,width,height):
        class Blend(C.Structure):_fields_=[('operation',W.BYTE),('flags',W.BYTE),('alpha',W.BYTE),('format',W.BYTE)]
        dst=W.POINT(self.x,self.y);src=W.POINT(0,0);size=W.SIZE(width,height);blend=Blend(0,0,255,1)
        if not self.u.UpdateLayeredWindow(self.hwnd,None,C.byref(dst),C.byref(size),self.dc,C.byref(src),0,C.byref(blend),2):raise C.WinError(C.get_last_error())

    def show(self):
        if type(self) is DesktopOverlay:
            if self.hud is None:self.hud=DesktopHUD(self.app)
            self.hud.owner=self
            self.hud.show()
        self.visible=True;self.runner.at=None;self.return_home_requested=True;self.last_signature=None;self.render();self.u.ShowWindow(self.hwnd,4)
        if getattr(self,'hud',None):self.u.SetWindowPos(self.hwnd,W.HWND(-1),0,0,0,0,0x0013)

    def hide(self):
        if getattr(self,'hud',None):self.hud.hide()
        self.visible=False;self.u.ShowWindow(self.hwnd,0)

    def close(self):
        if getattr(self,'hud',None):self.hud.close();self.hud=None
        self.visible=False
        if self.hwnd:self.u.DestroyWindow(self.hwnd);self.hwnd=None
        self._release_surface()
        for im in self.images.values():self.g.GdipDisposeImage(im)
        self.images.clear();self.g.GdiplusShutdown(self.token)
        self.u.UnregisterClassW(self.class_name,self.instance)

    def drain_actions(self):
        if getattr(self,'hud',None):self.hud.drain_actions()
        while not self.errors.empty():
            exc=self.errors.get()
            if hasattr(self.app,'debug'):self.app.debug.caught('Desktop native callback failure',exc)
            self.app.notice.set('A desktop error was saved in Diagnostics.')
        while not self.actions.empty():
            action,value=self.actions.get()
            if action=='home':self.app.return_to_pet_space()
            elif action=='hide':self.app.hide_desktop()
            elif action=='menu':self.app.desktop_menu()
            elif action=='scale':
                owner=getattr(self,'owner',self);owner.return_home_requested=True
                self.app.change_desktop_scale(value)
            elif action=='interact':self.app.interact(value)

    def _safe_wndproc(self,hwnd,msg,wp,lp):
        try:return self._wndproc(hwnd,msg,wp,lp)
        except Exception as exc:
            self.errors.put(exc)
            return self.u.DefWindowProcW(hwnd,msg,wp,lp)

    def _wndproc(self,hwnd,msg,wp,lp):
        # Native callbacks never call Tk, including after()/after_idle().
        if msg==0x20:
            mode=getattr(self.app,'desktop_interaction','click')
            point=W.POINT();self.u.GetCursorPos(C.byref(point))
            portal=self.portal_hit(point.x-self.x,point.y-self.y)
            zone=pet_zone(self.app.state.data['pet'],(point.x-self.x-SIDE)/(self.app.desktop_scale/100),(point.y-self.y)/(self.app.desktop_scale/100)-50)
            cursor=None if zone and portal is None else self.u.LoadCursorW(None,C.c_void_p(32649 if mode=='pet' or portal is not None else 32512))
            self.u.SetCursor(cursor);return 1
        if msg==0x21:return 3
        if msg==0x0201:
            point=W.POINT();self.u.GetCursorPos(C.byref(point))
            self.press=(C.c_short(lp&0xffff).value,C.c_short((lp>>16)&0xffff).value)
            self.portal_press=self.portal_hit(*self.press)
            self.was_running_on_press=self.runner.active
            self.drag_origin=(point.x,point.y,self.x,self.y);self.moved=False
            self.u.SetCapture(hwnd);return 0
        if msg==0x0200 and self.drag_origin and self.portal_press is None and getattr(self.app,'desktop_interaction','click')=='click':
            point=W.POINT();self.u.GetCursorPos(C.byref(point));sx,sy,ox,oy=self.drag_origin
            if abs(point.x-sx)+abs(point.y-sy)>5:self.moved=True
            if self.moved:
                self.x=ox+point.x-sx
                self._dock()
                if getattr(self,'hud',None):
                    self.hud.x=self.x-home_offset(self.app.desktop_scale,self.app.state.data['pet'],self.app.state.data)
                    self.hud._dock();self.x=self.hud.x+home_offset(self.app.desktop_scale,self.app.state.data['pet'],self.app.state.data)
                    self.y=self.hud.y;self.hud.last_signature=None;self.docked_to_hud=True
                self.u.SetWindowPos(hwnd,None,self.x,self.y,0,0,0x0015)
            return 0
        if msg==0x0202:
            had_press=self.drag_origin is not None
            self.u.ReleaseCapture();self.drag_origin=None
            x,y=C.c_short(lp&0xffff).value,C.c_short((lp>>16)&0xffff).value
            portal=self.portal_press;self.portal_press=None
            if had_press and self.moved and getattr(self,'hud',None):self.return_home_requested=True
            if had_press and not self.moved:
                if getattr(self,'was_running_on_press',False):self.return_home_requested=True
                if portal is not None:
                    if self.portal_hit(x,y)==portal:self.actions.put(('home' if portal==0 else 'hide',None))
                else:
                    mode=getattr(self.app,'desktop_interaction','click');scale=self.app.desktop_scale/100
                    zone=pet_zone(self.app.state.data['pet'],(x-SIDE)/scale,y/scale-50)
                    if zone and (mode=='click' or zone==mode):self.actions.put(('interact',mode))
            return 0
        if msg==0x0215:
            self.drag_origin=None;return 0
        if msg==0x020A:
            delta=C.c_short((wp>>16)&0xffff).value
            self.actions.put(('scale',25 if delta>0 else -25));return 0
        if msg==0x0205:
            self.actions.put(('menu',None));return 0
        return self.u.DefWindowProcW(hwnd,msg,wp,lp)


def full_counter(value):
    return str(max(0,int(value)))

def counter_panel_width(data):
    return max(100,round((16+8*max(len(full_counter(data[key])) for key in ('coins','moonstones','clicks','keystrokes')))/.70))

RESTING_LEFT={'Mochi':64,'Maple':62,'Clover':49,'Pip':67}

def counter_scale(percent):
    # Ten-pixel digit height at minimum, even with a half-size companion.
    return max(.85,clamp_scale(percent)/100)

def portal_size(percent):
    return round(52*max(.65,clamp_scale(percent)/100))

def hud_column_width(percent,data):
    return max(round(counter_panel_width(data)*counter_scale(percent)),2*portal_size(percent)+round(6*clamp_scale(percent)/100))

def home_offset(percent,pet,data):
    scale=clamp_scale(percent)/100
    return max(0,hud_column_width(percent,data)+round(6*scale)-SIDE-round(RESTING_LEFT[pet]*scale))

def hud_layout(percent,pet,data):
    width,height,_=layout(percent,pet);scale=clamp_scale(percent)/100
    panel_width=round(counter_panel_width(data)*counter_scale(percent));gap=round(6*scale)
    panel_height=round(58*counter_scale(percent));size=portal_size(percent)
    left=home_offset(percent,pet,data)+SIDE+round(RESTING_LEFT[pet]*scale)
    panel_x=left-gap-panel_width
    bottom=round(290*scale);portal_y=bottom-size
    second_y=portal_y-gap-panel_height;first_y=second_y-gap-panel_height
    panels=[(panel_x,first_y,panel_width,panel_height),(panel_x,second_y,panel_width,panel_height)]
    controls=[(left-gap-2*size-gap,portal_y,size,size),(left-gap-size,portal_y,size,size)]
    return width+home_offset(percent,pet,data),height,controls,panels

class DesktopHUD(DesktopOverlay):
    """Shared draggable home anchor; stays still only while the pet roams."""
    def portal_hit(self,x,y):
        return next((i for i,(bx,by,bw,bh) in enumerate(getattr(self,'controls',[])) if bx<=x<bx+bw and by<=y<by+bh),None)

    def render(self):
        if not self.visible:return
        a=self.app;data=a.state.data;pet=data['pet']
        width,height,self.controls,panels=hud_layout(a.desktop_scale,pet,data)
        first=not hasattr(self,'width');anchor=self.x
        if not self.dc or (self.width,self.height)!=(width,height):
            self._resize(width,height);self.x=anchor
        self._dock()
        if first:self.x=getattr(self,'work_area',(0,0,0,0))[0]+8
        signature=(pet,a.desktop_scale,self.x,self.y,tuple(data[key] for key in ('coins','moonstones','clicks','keystrokes')))
        if signature==self.last_signature:return
        self.check(self.g.GdipGraphicsClear(self.graphics,0))
        for slug,rect in zip(CONTROL_ITEMS[pet],self.controls):self._draw_image(a.art_dir/f'item-{slug}.png',rect)
        for rect,panel,keys in zip(panels,('wallet','activity'),(('coins','moonstones'),('clicks','keystrokes'))):
            x0,y,w,h=rect
            self._draw_image(a.art_dir/f'desktop-{panel}-panel.png',rect)
            for row,key in enumerate(keys):
                number=full_counter(data[key]);scale=counter_scale(a.desktop_scale);digit_w=round(8*scale);digit_h=round(12*scale)
                inset=round(w*20/72);x=x0+inset+(w-inset-round(4*scale)-len(number)*digit_w)//2
                for character in number:
                    self._draw_image(a.art_dir/f'wallet-digit-{character}.png',(x,y+round((17+row*21)*scale),digit_w,digit_h));x+=digit_w
        self.check(self.g.GdipFlush(self.graphics,1));self.present(width,height);self.last_signature=signature

    def _wndproc(self,hwnd,msg,wp,lp):
        if msg==0x20:
            self.u.SetCursor(self.u.LoadCursorW(None,C.c_void_p(32649)));return 1
        if msg==0x21:return 3
        x,y=C.c_short(lp&0xffff).value,C.c_short((lp>>16)&0xffff).value
        if msg==0x0201:
            point=W.POINT();self.u.GetCursorPos(C.byref(point))
            self.portal_press=self.portal_hit(x,y);self.drag_origin=(point.x,point.y,self.x,self.y);self.moved=False
            self.u.SetCapture(hwnd);return 0
        if msg==0x0200 and self.drag_origin:
            point=W.POINT();self.u.GetCursorPos(C.byref(point));sx,sy,ox,oy=self.drag_origin
            if abs(point.x-sx)+abs(point.y-sy)>5:self.moved=True
            if self.moved:
                self.x=ox+point.x-sx;self._dock();self.last_signature=None
                owner=getattr(self,'owner',None)
                if owner:owner.return_home_requested=True;owner.docked_to_hud=True;owner.group_adjust_until=time.monotonic()+3
                self.u.SetWindowPos(hwnd,None,self.x,self.y,0,0,0x0015)
            return 0
        if msg==0x0202:
            had_press=self.drag_origin is not None
            pressed=self.portal_press;self.portal_press=None;self.drag_origin=None;self.u.ReleaseCapture()
            if had_press and not self.moved and pressed is not None and self.portal_hit(x,y)==pressed:self.actions.put(('home' if pressed==0 else 'hide',None))
            return 0
        if msg==0x0215:self.portal_press=None;self.drag_origin=None;return 0
        if msg==0x020A:
            delta=C.c_short((wp>>16)&0xffff).value
            self.actions.put(('scale',25 if delta>0 else -25));return 0
        if msg==0x0205:self.actions.put(('menu',None));return 0
        return self.u.DefWindowProcW(hwnd,msg,wp,lp)
