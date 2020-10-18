from receiver import amqp__ini__
import uvicorn
import eventlet
import socketio
import sys
import os
from sender import sender
from models.models import Message
import threading
import json
import requests
from logger.logger import Logger
import pika

PORT = 0
TOWER = ""
sio = socketio.Server(cors_allowed_origins="*")
app = socketio.WSGIApp(sio)
MESSAGE = {'message': '', 'tower': '', 'sender': '', 'health': 0, 'shield': 0}
MESSAGE_ATTACKED = {'message': '', 'Hocus': 0,
                    'Pocus': 0, 'Hocus Defenders': 0, 'Pocus Defenders': 0}

logger = None


# ON CONNECT EVENT
@ sio.event
def connect(sid, environ):
    logger.log_info(f"CONNECT EVENT RAISED SIO: {sio}")
    MESSAGE['message'] = 'connect'
    MESSAGE['tower'] = TOWER
    sender.send(MESSAGE, ["Restlin"])
    sio.enter_room(sid, TOWER)


# ON ATTACK EVENT
@ sio.event
def attack(sid, nickname):
    logger.log_info(f"ATTACK EVENT RAISED FROM USER {nickname}")
    MESSAGE['message'] = 'attack'
    MESSAGE['tower'] = TOWER
    MESSAGE['sender'] = nickname
    sender.create_consumer(TOWER)
    response = sender.send_with_ack(MESSAGE, "Hocus" if TOWER ==
                                    "Pocus" else "Pocus")
    response = json.loads(response)
    MESSAGE_ATTACKED['message'] = 'health_update'
    MESSAGE_ATTACKED[response['tower']] = response['health']
    MESSAGE_ATTACKED[TOWER] = -5000
    MESSAGE_ATTACKED[response['tower'] + ' Defenders'] = -5000
    MESSAGE_ATTACKED[TOWER + ' Defenders'] = -5000
    sio.emit(MESSAGE_ATTACKED, room=TOWER)
    print(f"EMMITED INTERNALY {MESSAGE_ATTACKED}")
    sender.send(MESSAGE, ["Restlin"])


# ON DEFEND EVENT
@ sio.event
def defend(sid, nickname):
    logger.log_info(f"DEFEND EVENT RAISED FROM USER {nickname}")
    MESSAGE['message'] = 'shield'
    MESSAGE['tower'] = TOWER
    MESSAGE['sender'] = nickname
    sio.emit(MESSAGE['message'], room=TOWER)
    sender.send(MESSAGE, ['Restlin'])


# ON DISCONNECT EVENT
@ sio.event
def disconnect(sid):
    logger.log_info(f"DISCONNECT EVENT RAISED WITH SID {sid}")
    MESSAGE['message'] = 'disconnect'
    MESSAGE['tower'] = TOWER
    MESSAGE['sender'] = sid
    sender.send(MESSAGE, ['Restlin'])
    sio.leave_room(sid, TOWER)


def start_elf(_app, _PORT):
    eventlet.wsgi.server(eventlet.listen(('localhost', _PORT)), _app)


# DEFINING AMQP CONSUMER CALLBACK AND STARTING CONSUMER
def start_amqp(sio):

    print(f"Started amqp")

    def amqp_callback(ch, method, properties, body):
        message = json.loads(body)
        # on connected
        if(message['message'] == 'connect' or message['message'] == 'disconnect'):
            message['message'] = 'health_update'
            sio.emit(message['message'], message, room=TOWER)
            logger.log_info(f"EMITTED INTERNALY {message['message']}")
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
            message['health'] = data['health']
            message['shield'] = data['shield']

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
            routing_key = "Hocus" if TOWER == "Pocus" else "Pocus"

            # SET SHIELD OF NEW MESSAGE TO BE 0 BECAUSE ON RESPONSE WE DON'T ATTACKER TO KNOW OUR SHIELD
            message['shield'] = 0
            ch.basic_publish(exchange="Rabbit", routing_key=routing_key,
                             properties=pika.BasicProperties(
                                 correlation_id=properties.correlation_id),
                             body=json.dumps(message))
            # acknowledge this to oponent that attacked you by sending HP

        # on defend
        elif(message['message'] == 'defend'):
            message['message'] = 'shield'
            sio.emit(message['message'], room=TOWER)
            requests.put('http://localhost:1337/tower', data=message)

            logger.log_info(f"EMITTED INTERNALY {message['message']}")

    amqp__ini__(routing_key=TOWER, amqp_callback=amqp_callback)


if __name__ == '__main__':
    try:
        PORT = int(sys.argv[1])
        logger = Logger(filename=f"tower{PORT}.log")
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
