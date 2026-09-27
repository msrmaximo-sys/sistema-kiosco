@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Falta el entorno virtual .venv. Segui la instalacion del README.md.
    pause
    exit /b 1
)
echo Iniciando el sistema del kiosco...
".venv\Scripts\python.exe" -m streamlit run app.py --server.address 127.0.0.1
if errorlevel 1 (
    echo No se pudo iniciar el sistema. Revisa el error y las dependencias del README.md.
    pause
    exit /b 1
)
endlocal
