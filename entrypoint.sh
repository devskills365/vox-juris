#!/bin/bash
echo "Utilisateur actuel : $(whoami)"
echo "Ajustement des permissions..."
chmod -R 777 /app/instance /app/static/uploads /app/static/profile_pictures /app/static/pdfs
ls -l /app/instance
echo "Démarrage de Gunicorn..."
exec gunicorn --bind 0.0.0.0:5000 --timeout 120 app:app