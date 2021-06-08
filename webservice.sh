#!/bin/sh
cd /home/web
export REDIS_URL=$REDIS_URL
gunicorn -b 0.0.0.0:5000 --access-logfile - --error-logfile - webservice:app