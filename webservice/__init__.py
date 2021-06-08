import os
from flask import Flask
from flask_redis import FlaskRedis

app = Flask(__name__)
app.config['REDIS_URL'] = os.environ.get('REDIS_URL', "redis://localhost:6379/0")
redis_client = FlaskRedis(app)

from webservice import routes