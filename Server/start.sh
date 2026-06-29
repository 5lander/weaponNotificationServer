#!/usr/bin/env bash
# Arranque local en frío (Linux / macOS / Git Bash)
# Borra todas las sesiones ANTES de levantar el servidor para que el
# reinicio exija login manual, y luego ejecuta runserver.
#
# Uso:  bash start.sh   (desde la carpeta Server)
set -o errexit

cd "$(dirname "$0")"

python manage.py flush_all_sessions
python manage.py runserver
