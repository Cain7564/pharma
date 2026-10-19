@echo off
chcp 65001 >nul
cd /d "%~dp0"
call venv\Scripts\activate.bat
echo Revisando avisos a clientes cada hora. Deja esta ventana abierta. Ctrl + C para detener.
python manage.py enviar_recordatorios --cada 3600
pause
