#!/bin/sh
cd /home/net_stats
. venv/bin/activate
gunicorn -b 0.0.0.0:5000 --access-logfile - --error-logfile - webservice:app