@echo off
REM Le Bordel Francais : demarre le studio (worker de production + tableau de bord).
REM Double-clic suffit. Pour un demarrage automatique a l'ouverture de session : scripts\installer_demarrage_auto.ps1
cd /d "%~dp0"
set PYTHONUTF8=1
if not exist .env copy .env.example .env >nul
start "LBF - worker" /min python -m lbf.worker --loop
start "LBF - tableau de bord" /min python -m dashboard.app
if /i "%1"=="auto" goto :eof
timeout /t 3 >nul
start "" http://127.0.0.1:8765/
