@echo off
setlocal
where winget >nul 2>nul
if errorlevel 1 (
  echo Install Microsoft App Installer from Microsoft Store, then retry.
  exit /b 1
)
winget install --id Python.Python.3.12 --exact --source winget
winget install --id Gyan.FFmpeg --exact --source winget
winget install --id Git.Git --exact --source winget
echo Close and reopen Terminal after installation, then run: py -3 momentmeter.py check
echo Windows built-in English speech is used. No paid speech service is required.
pause
