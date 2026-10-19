#!/usr/bin/env bash
# Inicia el proyecto en Mac o Linux:  bash iniciar.sh
set -e
cd "$(dirname "$0")"
PY=python3
command -v python3 >/dev/null 2>&1 || PY=python

[ -d venv ] || { echo "Creando el entorno virtual, un momento..."; $PY -m venv venv; }
source venv/bin/activate
echo "Instalando lo necesario..."
pip install -r requirements.txt --disable-pip-version-check -q
python manage.py preparar

echo
echo "=========================================================="
echo " Sitio:  http://127.0.0.1:8000"
echo " Panel:  http://127.0.0.1:8000/panel/"
echo " Para apagar el servidor presiona Ctrl + C"
echo "=========================================================="
python manage.py runserver
