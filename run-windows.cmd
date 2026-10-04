@echo off
setlocal
cd /d "%~dp0"
py -3 momentmeter.py %*
exit /b %errorlevel%
