#!/bin/sh

echo "Aguardando banco..."
sleep 10

echo "Aplicando migrations..."
python manage.py migrate

echo "Subindo servidor..."
python manage.py runserver 0.0.0.0:8000