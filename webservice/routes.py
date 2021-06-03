import json
from flask import jsonify, abort, Response
from webservice import app, redis_client

INTEGER_FIELDS = ["sent", "recv"]
FLOAT_FIELDS = ["up", "down", "ping", "time"]

def cleanup_speed_data(speed_data: dict) -> dict:
    new_data = {}
    for key, val in speed_data.items():
        new_data[key.decode()] = val.decode()
    for field in INTEGER_FIELDS:
        if not field in new_data:
            continue
        new_data[field] = int(new_data[field])
    for field in FLOAT_FIELDS:
        if not field in new_data:
            continue
        new_data[field] = float(new_data[field])
    new_data['server_info'] = json.loads(new_data['server_info'])
    return new_data

def cleanup_latency(latency: dict) -> dict:
    new_latency = {}
    for key, val in latency.items():
        new_latency[key.decode()] = float(val.decode())
    return new_latency

@app.route('/')
@app.route('/api')
@app.route('/api/v1')
def hello():
    return "Hi"

@app.route('/api/v1/speed')
def get_speed():
    speed_data = redis_client.hgetall('speedtest')
    if not speed_data:
        resp = Response('', 204)
        return resp
    else:
        speed_data = cleanup_speed_data(speed_data)
    print(speed_data)
    return jsonify(speed_data)

@app.route('/api/v1/speed_simple')
def get_speed_simple():
    speed_data = redis_client.hgetall('speedtest')
    if not speed_data:
        resp = Response('', 204)
        return resp
    else:
        speed_data = cleanup_speed_data(speed_data)
    if 'server_info' in speed_data:
        del speed_data['server_info']
    print(speed_data)
    return jsonify(speed_data)

@app.route('/api/v1/latency', defaults={"host": "combined"})
@app.route('/api/v1/latency/<host>')
def get_latency(host):
    if host.casefold() == 'all'.casefold():
        host = 'combined'
    data = redis_client.hgetall(host)
    if not data:
        resp = Response('', 204)
        return resp
    return_dat = {
        "endpoint": host
    }
    return_dat.update(cleanup_latency(data))
    return jsonify(return_dat)
