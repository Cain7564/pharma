@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PY=python
where py >nul 2>nul && set PY=py

if not exist venv\Scripts\activate.bat (
  echo Creando el entorno virtual, un momento...
  %PY% -m venv venv
  if errorlevel 1 (
    echo No se pudo crear el entorno. Instala Python 3.12 o superior desde python.org
    echo y marca "Add Python to PATH" durante la instalacion.
    pause
    exit /b 1
  )
)

call venv\Scripts\activate.bat
echo Instalando lo necesario...
pip install -r requirements.txt --disable-pip-version-check -q
python manage.py preparar
if errorlevel 1 ( pause & exit /b 1 )

echo.
echo ==========================================================
echo  Sitio:  http://127.0.0.1:8000
echo  Panel:  http://127.0.0.1:8000/panel/
echo  Para apagar el servidor presiona Ctrl + C
echo ==========================================================
python manage.py runserver
pause
