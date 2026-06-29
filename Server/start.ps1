# Arranque local en frío (Windows / PowerShell)
# Borra todas las sesiones ANTES de levantar el servidor para que el
# reinicio exija login manual, y luego ejecuta runserver.
#
# Uso:  ./start.ps1   (desde la carpeta Server)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

python manage.py flush_all_sessions
python manage.py runserver
