@echo off
setlocal
where py >nul 2>nul
if errorlevel 1 (
  python -B "%~dp0installer.py" install %*
) else (
  py -3 -B "%~dp0installer.py" install %*
)
if errorlevel 1 echo Command failed. Read the error above. Python 3.9+ must be installed.
pause
