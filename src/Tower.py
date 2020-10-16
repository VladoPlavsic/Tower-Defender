from receiver import amqp__ini__
import uvicorn
import eventlet
import socketio
from socketio import Server
import sys
import os
from sender import sender
from models.models import Item, Message, Towermodel
import threading
import json
import requests

PORT = 0
TOWER = ""
global sio
sio = socketio.Server(cors_allowed_origins="*")
app = socketio.WSGIApp(sio)
MESSAGE = {'message': '', 'tower': '', 'sender': '', 'health': 0, 'shield': 0}


@ sio.event
def connect(sid, environ):
    print("*******************")
    print(f"CONNECT EVENT RAISED SIO: {sio}")
    print("*******************")
    MESSAGE['message'] = 'connect'
    MESSAGE['tower'] = TOWER
    sender._send(MESSAGE, ["Restlin"])
    sio.enter_room(sid, TOWER)


@ sio.event
def attack(sid, nickname, towername):
    print("*******************")
    print(f"ATTACK EVENT RAISED FROM USER {nickname}")
    print("*******************")
    MESSAGE['message'] = 'attack'
    MESSAGE['tower'] = towername
    MESSAGE['sender'] = nickname
    sender._send(MESSAGE, ["Hocus", "Restlin"] if towername ==
                 "Pocus" else ["Pocus", "Restlin"])


@ sio.event
def defend(sid, nickname, towername):
    print("*******************")
    print(f"DEFEND EVENT RAISED FROM USER {nickname}")
    print("*******************")
    MESSAGE['message'] = 'shield'
    MESSAGE['tower'] = towername
    MESSAGE['sender'] = nickname
    sio.emit(MESSAGE['message'], room=TOWER)
    sender._send(MESSAGE, ['Restlin'])


@ sio.event
def disconnect(sid):
    print("*******************")
    print(f"DISCONNECT EVENT RAISED WITH SID {sid}")
    print("*******************")
    MESSAGE['message'] = 'disconnect'
    MESSAGE['tower'] = TOWER
    MESSAGE['sender'] = sid
    sender._send(MESSAGE, ['Restlin'])
    sio.leave_room(sid, TOWER)


def start_elf(_app, _PORT):
    eventlet.wsgi.server(eventlet.listen(('localhost', _PORT)), _app)


def start_amqp(sio):

    print(f"Started amqp")

    def amqp_callback(ch, method, properties, body):
        message = json.loads(body)
        # on connected
        if(message['message'] == 'connect' or message['message'] == 'disconnect'):
            message['message'] = 'health_update'
            sio.emit(message['message'], message, room=TOWER)

            print("*******************")
            print(f"EMITTED INTERNALY {message['message']}")
            print("*******************")
        # on atacked
        elif(message['message'] == 'attack'):
            message['message'] = 'health_attacked'
            message['tower'] = TOWER
            sio.emit(message['message'], room=TOWER)
            # data['health'] = towerHealth \\ data['shield'] = towerDefense
            data = requests.get('http://localhost:1337/tower',
                                data=json.dumps({"nickname": TOWER}))
            data = json.loads(data.content)

            data['shield'] -= 100

            if(data['shield'] < 0):
                data['health'] += data['shield']
                data['shield'] = 0
                message['shield'] = data['shield']
                message['health'] = data['health']
                requests.put('http://localhost:1337/tower',
                             data=json.dumps(message))

            else:
                requests.put('http://localhost:1337/tower',
                             data=json.dumps(message))

            # acknowledge this to oponent that attacked you by sending HP
            '''
            print("*******************")
            print(f"EMITTED INTERNALY {message['message']}")
            print("*******************")
            '''
        # on defend
        elif(message['message'] == 'defend'):
            message['message'] = 'shield'
            sio.emit(message['message'], room=TOWER)
            requests.put('http://localhost:1337/tower', data=message)

            print("*******************")
            print(f"EMITTED INTERNALY {message['message']}")
            print("*******************")

        # ON ACKNOWLEDGEMENT THAT YOU'VE BEEN ATTACKED FROM OPONENT

    amqp__ini__(routing_key=TOWER, amqp_callback=amqp_callback)


if __name__ == '__main__':
    try:
        PORT = int(sys.argv[1])
        TOWER = "Hocus" if PORT == 666 else "Pocus"
        amqp = threading.Thread(target=start_amqp, args=(sio,))
        elf = threading.Thread(target=start_elf, args=(app, PORT))
        # uvicorn.run(app, host='localhost', port=PORT)
        # eventlet.wsgi.server(eventlet.listen(('localhost', PORT)), app)
        elf.start()
        amqp.start()
    except KeyboardInterrupt:
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
