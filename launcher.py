"""Install diagnostics before importing game code or loading artwork."""
from diagnostics import Diagnostics

def main():
    debug=Diagnostics();debug.install()
    import tkinter as tk
    root=None
    try:
        from game import App
        root=tk.Tk()
        def startup_callback(t,e,tb):debug.report('Startup interface exception',t,e,tb)
        root.report_callback_exception=startup_callback
        app=App(root);debug.attach(app)
        root.mainloop()
    except Exception as exc:
        path=debug.caught('Startup or main loop failure',exc)
        print(f'Little Companions could not continue. Report saved at: {path}\nRun Debug-Windows.bat to export it.')
        import traceback
        traceback.print_exc()
        return 1
    finally:
        if root:
            try:root.destroy()
            except tk.TclError:pass
        debug.close()
    return 0

if __name__=='__main__':raise SystemExit(main())
