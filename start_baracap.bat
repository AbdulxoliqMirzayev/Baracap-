@echo off
setlocal
set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python312\python.exe"

if not exist "%PYTHON_EXE%" (
  echo Python 3.12 topilmadi: %PYTHON_EXE%
  echo Pythonni o'rnating yoki PATH ichiga python qo'shing.
  pause
  exit /b 1
)

set "PORT=8000"
set "APP_HOST=127.0.0.1"

echo Eski AI Agent/local serverlar to'xtatilmoqda...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ports = 8000,8001,8002,8003,8004,3000,3001,3002,5173; " ^
  "$listeners = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -in $ports }; " ^
  "$listenerIds = @($listeners | Select-Object -ExpandProperty OwningProcess -Unique); " ^
  "$oldProjectIds = @(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*C:\AI Agents platform\*' -or $_.CommandLine -like '*C:\AI Container\*' -or $_.CommandLine -like '*C:\Taklifnoma\*' } | Select-Object -ExpandProperty ProcessId); " ^
  "$ids = @($listenerIds + $oldProjectIds | Where-Object { $_ } | Select-Object -Unique); " ^
  "foreach ($id in $ids) { Stop-Process -Id $id -Force -ErrorAction SilentlyContinue }; " ^
  "Start-Sleep -Milliseconds 600"

"%PYTHON_EXE%" -m pip install -r requirements.txt
"%PYTHON_EXE%" main.py
