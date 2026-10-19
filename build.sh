#!/usr/bin/env bash
# Script de construcción para Render (se ejecuta en cada despliegue).
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate --noinput
python manage.py crear_admin

if [ "${CARGAR_EJEMPLOS:-0}" = "1" ]; then
  python manage.py cargar_ejemplos
fi
