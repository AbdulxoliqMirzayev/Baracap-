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

"%PYTHON_EXE%" -m pip install -r requirements.txt
"%PYTHON_EXE%" main.py
