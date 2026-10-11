@echo off
cd /d "%~dp0"
py -3 diagnostics.py
if errorlevel 1 (
  echo.
  echo Diagnostics could not open. Copy the error above into our chat.
  pause
)
