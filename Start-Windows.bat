@echo off
cd /d "%~dp0"
py -3 launcher.py
if errorlevel 1 (
  echo.
  echo Startup failed. Read the error above or run Debug-Windows.bat.
  echo If Python is missing, install Python 3.12 or newer with Tcl/Tk.
  pause
)
