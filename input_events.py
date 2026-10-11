"""Optional Windows event hooks. Store action categories only, never key data."""
import ctypes
import queue
import sys


class BackgroundInput:
    def __init__(self):
        self.events = queue.SimpleQueue()
        self.hooks = []
        self.callbacks = []

    def start(self):
        if sys.platform != 'win32':
            return False
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
        self.user32 = user32
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
                self.stop()
                return False
            self.hooks.append(handle)
        return True

    def stop(self):
        for handle in self.hooks:
            self.user32.UnhookWindowsHookEx(handle)
        self.hooks.clear()
        self.callbacks.clear()
        while not self.events.empty():
            self.events.get_nowait()

    def drain(self):
        while True:
            try:
                yield self.events.get_nowait()
            except queue.Empty:
                return
