@echo off
cd /d "%~dp0"
py -3 -c "import webview" >nul 2>&1
if errorlevel 1 py -3 -m pip install -r requirements.txt
if errorlevel 1 goto error
start "" pyw -3 desktop.pyw
exit /b
:error
if errorlevel 1 pause
