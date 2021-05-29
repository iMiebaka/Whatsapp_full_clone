#!/bin/sh

cd /home/imiebaka/Documents/Python_Project/Channels
source env/bin/activate
python manage.py makemigrations
python manage.py migrate

