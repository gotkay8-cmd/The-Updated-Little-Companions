"""Optional Windows event hooks. Store action categories only, never key data."""
import ctypes
import queue
import sys
import threading


class BackgroundInput:
    def __init__(self):
        self.events = queue.SimpleQueue()
        self.hooks = []
        self.callbacks = []
        self.thread = None
        self.thread_id = None
        self.ready = threading.Event()
        self.stopping = threading.Event()
        self.started = False
        self.last_error = ''

    def start(self):
        if sys.platform != 'win32':
            return False
        self.stop()
        if self.thread and self.thread.is_alive():
            return False
        self.ready.clear()
        self.stopping.clear()
        self.started = False
        self.last_error = ''
        self.thread = threading.Thread(target=self._run, name='Companion activity', daemon=True)
        self.thread.start()
        if not self.ready.wait(3):
            self.last_error = 'Windows activity listener did not start in time.'
            self.stop()
            return False
        return self.started

    @property
    def running(self):
        return bool(self.started and self.thread and self.thread.is_alive())

    def _run(self):
        """Keep Windows callbacks responsive independently of Tk and PNG work."""
        try:
            self._listen()
        except Exception as exc:
            self.last_error = str(exc)
        finally:
            for handle in self.hooks:
                self.user32.UnhookWindowsHookEx(handle)
            self.hooks.clear()
            self.callbacks.clear()
            self.started = False
            self.thread_id = None
            self.ready.set()

    def _listen(self):
        from ctypes import wintypes
        user32 = ctypes.WinDLL('user32', use_last_error=True)
        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        callback_type = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_int,
                                          wintypes.WPARAM, wintypes.LPARAM)
        user32.SetWindowsHookExW.argtypes = [ctypes.c_int, callback_type, wintypes.HINSTANCE, wintypes.DWORD]
        user32.SetWindowsHookExW.restype = wintypes.HANDLE
        user32.CallNextHookEx.argtypes = [wintypes.HANDLE, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
        user32.CallNextHookEx.restype = ctypes.c_ssize_t
        user32.UnhookWindowsHookEx.argtypes = [wintypes.HANDLE]
        user32.UnhookWindowsHookEx.restype = wintypes.BOOL
        kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
        kernel32.GetModuleHandleW.restype = wintypes.HMODULE
        kernel32.GetCurrentThreadId.restype = wintypes.DWORD
        user32.PeekMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT, wintypes.UINT]
        user32.PeekMessageW.restype = wintypes.BOOL
        user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
        user32.GetMessageW.restype = ctypes.c_int
        user32.PostThreadMessageW.argtypes = [wintypes.DWORD, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        user32.PostThreadMessageW.restype = wintypes.BOOL
        self.user32 = user32
        # Create this thread's message queue before exposing its ID to stop().
        message = wintypes.MSG()
        user32.PeekMessageW(ctypes.byref(message), None, 0, 0, 0)
        self.thread_id = kernel32.GetCurrentThreadId()
        module = kernel32.GetModuleHandleW(None)
        for hook_type, messages, category in (
                (13, (0x100, 0x104), 'typing'),
                (14, (0x201, 0x204, 0x207, 0x20B), 'wave')):
            def callback(code, message, data, messages=messages, category=category):
                # Do not dereference data: no keycodes, text, or pointer positions.
                if code >= 0 and message in messages:
                    self.events.put(category)
                return user32.CallNextHookEx(None, code, message, data)
            wrapped = callback_type(callback)
            self.callbacks.append(wrapped)
            handle = user32.SetWindowsHookExW(hook_type, wrapped, module, 0)
            if not handle:
                self.last_error = f'Windows activity hook failed ({ctypes.get_last_error()}).'
                return
            self.hooks.append(handle)
        if self.stopping.is_set():
            return
        self.started = True
        self.ready.set()
        while not self.stopping.is_set():
            result = user32.GetMessageW(ctypes.byref(message), None, 0, 0)
            if result <= 0:
                if result < 0:self.last_error = 'Windows activity message loop failed.'
                break

    def stop(self):
        self.stopping.set()
        if self.thread_id is not None:
            self.user32.PostThreadMessageW(self.thread_id, 0x12, 0, 0)
        if self.thread and self.thread is not threading.current_thread():
            self.thread.join(timeout=2)
        while not self.events.empty():
            self.events.get_nowait()

    def drain(self):
        while True:
            try:
                yield self.events.get_nowait()
            except queue.Empty:
                return
