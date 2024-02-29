#!/usr/bin/python3 -u
import struct

import paho.mqtt.client as mqtt
import time
import base64
import shodan
import socket
import json
import os
import PngConverter
import zlib
import os
import flask

devices = {}

next_target_update = 0

update_timestamp = None

app = flask.Flask(__name__)

if not os.environ.get('SHODAN_TOKEN'):
    print('env variable SHODAN_TOKEN required for shodan API access')
    exit(1)

@app.get('/')
def root():
    return flask.redirect('/vacs')

@app.get('/vacs')
def get_vacs():
    return flask.render_template('vacs.html.jinja2', devices=devices.values()), {
        'Refresh': 2
    }

@app.post('/vacs/all')
def vac_control_all():
    command = flask.request.form['command']
    broadcast_command(command)
    return root()

@app.post('/vacs/<path:id>')
def vac_control_single(id: str):
    command = flask.request.form['command']
    endpoint = flask.request.form['endpoint']
    publish(id, endpoint, command)
    return root()

@app.post('/update')
def update():
    global devices

    devices = {}

    targets_update()

    return "targets updated"


def connect_client(host, port):
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    def on_connect(client, userdata, flags, reason_code, properties):
        print(f'connected to {client.host} ({reason_code})')
        client.subscribe('valetudo/+/StatusStateAttribute/status')
        client.subscribe('valetudo/+/MapData/map-data')

    def on_message(client, userdata_, message):
        try:
            parts = message.topic.split('/')

            valetudo_base, robot_name, capability, endpoint = parts[:4]

            device_identifier = f'{host}:{port}/{robot_name}'

            device = devices.get(device_identifier)

            if device is None:
                device = devices[device_identifier] = {
                    'mqtt': client,
                    'identifier': device_identifier,
                    'map': '',
                    'state': 'unknown',
                    'topic_base': f'{valetudo_base}/{robot_name}'
                }

            if (capability, endpoint) == ('MapData', 'map-data'):
                print(f'{device_identifier} map changed')
                map_data = json.loads(zlib.decompress(message.payload))
                map_png = PngConverter.convert_map_data_to_png(map_data)
                device['map'] = base64.b64encode(map_png).decode('utf-8')
            elif (capability, endpoint) == ('StatusStateAttribute', 'status'):
                print(f'{device_identifier} state changed')
                json_string = message.payload.decode('utf-8')
                device['state'] = json_string

            global update_timestamp
            update_timestamp = time.strftime('%a, %d %b %G %H:%M:%S GMT')

        except Exception as e:
            pass

    def on_subscribe(client, userdata, mid, reason_code_list, properties):
        print(f'subscribed {mid}')

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_subscribe = on_subscribe

    client.connect(host, port)

    client.loop_start()
    return client


def publish(target, endpoint, payload):
    try:
        client = devices[target]['mqtt']
        client.publish(f'{devices[target]["topic_base"]}/{endpoint}/set', payload)
    except:
        print(f'error publishing to client {target}')


def send_command(target, command):
    publish(target, 'operation', bytes(command, 'utf-8'))


def broadcast_command(command):
    for target in devices:
        send_command(target, command)


def targets_update(target_host=None):
    api = shodan.client.Shodan(os.environ['SHODAN_TOKEN'])
    results = api.search('valetudo mqtt')

    for result in results['matches']:
        host = socket.inet_ntoa(struct.pack('!L', result['ip']))
        if target_host is not None and host != target_host:
            continue
        port = result['port']
        device_identifier = f'{host}:{port}'

        try:
            print(f'connecting to {device_identifier}')
            client = connect_client(host, port)
        except Exception as e:
            print(f"failed connecting to {device_identifier}")

targets_update()