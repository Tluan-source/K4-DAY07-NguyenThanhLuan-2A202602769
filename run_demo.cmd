@echo off
setlocal
cd /d "%~dp0"

set "DEMO_URL=http://127.0.0.1:8766/src/demo.html"
set "HEALTH_URL=http://127.0.0.1:8766/api/health"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Khong tim thay .venv\Scripts\python.exe
    echo Hay tao moi truong ao va cai requirements.txt truoc khi chay demo.
    pause
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='SilentlyContinue'; try { $r=Invoke-RestMethod '%HEALTH_URL%' -TimeoutSec 1; if($r.status -eq 'ready'){ exit 0 } } catch {}; exit 1"

if not errorlevel 1 goto ready

echo Dang khoi dong RAG demo...
start "RAG Demo Server" /D "%~dp0" "%~dp0.venv\Scripts\python.exe" "%~dp0demo_server.py"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='SilentlyContinue'; for($i=0; $i -lt 30; $i++){ try { $r=Invoke-RestMethod '%HEALTH_URL%'; if($r.status -eq 'ready'){ exit 0 } } catch {}; Start-Sleep -Milliseconds 250 }; exit 1"

if errorlevel 1 (
    echo [ERROR] Server khong san sang tai %HEALTH_URL%
    echo Xem cua so RAG Demo Server de biet chi tiet.
    pause
    exit /b 1
)

:ready
echo Demo da san sang: %DEMO_URL%
if /I "%~1"=="--no-browser" exit /b 0
start "" "%DEMO_URL%"
endlocal
