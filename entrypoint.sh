#!/bin/sh

echo "Aguardando banco..."

while ! nc -z db 5432; do
  sleep 1
done

echo "Banco disponível!"

echo "Aplicando migrations..."
python manage.py migrate

echo "Subindo servidor..."
python manage.py runserver 0.0.0.0:8000