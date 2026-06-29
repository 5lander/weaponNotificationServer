#!/usr/bin/env bash
# Render build script - Weapon Detection System
# Se ejecuta en cada deploy dentro de la red de Render, donde la BD si conecta.
# Invocar como Build Command:  bash Server/build.sh
set -o errexit

# Entra a la carpeta Server sin importar desde donde se invoque
cd "$(dirname "$0")"

# --only-binary=pillow evita compilar Pillow desde fuente en Render
pip install --only-binary=pillow -r requirements.txt

# Crea las tablas en la BD PostgreSQL de Render (auth_user, etc.)
python manage.py migrate --noinput

# Archivos estaticos
python manage.py collectstatic --noinput
