import uvicorn
import eventlet
import socketio
from socketio import Server
import sys
import os
from sender import sender
from models.models import Item, Message
import threading
from receiver import amqp__ini__
import json

PORT = 0
TOWER = ""
sio = socketio.Server(cors_allowed_origins="*")
app = socketio.WSGIApp(sio)
MESSAGE = {'message': '', 'tower': '', 'sender': ''}


'''

emit:
health
shield
oponent_health

'''


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
    MESSAGE['message'] = 'defend'
    MESSAGE['tower'] = towername
    MESSAGE['sender'] = nickname
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


def start_amqp():

    print(f"Started amqp")

    def amqp_callback(ch, method, properties, body):
        message = json.loads(body)
        if(message["message"] != 'defense'):
            print("*******************")
            print(
                f"EMITING INTERNALY WITH MESSAGE {message['message']} SIO: {sio}")
            print("*******************")
            sio.emit(message["message"], message, room=TOWER)

    amqp__ini__(routing_key=TOWER, amqp_callback=amqp_callback)


if __name__ == '__main__':
    try:
        PORT = int(sys.argv[1])
        TOWER = "Hocus" if PORT == 666 else "Pocus"
        amqp = threading.Thread(target=start_amqp)
        amqp.start()
        # uvicorn.run(app, host='localhost', port=PORT)
        eventlet.wsgi.server(eventlet.listen(('localhost', PORT)), app)
    except KeyboardInterrupt:
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
