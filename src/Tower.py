'''
TO START
python3 Tower.py <port-number> (SHOULD BE 666 or 999)
'''
from receiver import amqp__ini__
import uvicorn
import socketio
import sys
import os
from sender import sender
import threading
import json
import requests
from logger.logger import Logger
import pika
import asyncio

PORT = 0
TOWER = ""
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins="*")
app = socketio.ASGIApp(sio)
MESSAGE = {'message': '', 'tower': '', 'sender': '', 'health': 0, 'shield': 0}
MESSAGE_ATTACKED = {'message': '', 'Hocus': 0,
                    'Pocus': 0, 'Hocus Defenders': 0, 'Pocus Defenders': 0}

logger = None


# ON CONNECT EVENT
@ sio.event
async def connect(sid, environ):
    logger.log_info(f"CONNECT EVENT RAISED WITH SID: {sio}")
    MESSAGE['message'] = 'connect'
    MESSAGE['tower'] = TOWER
    sender.send(MESSAGE, ["Restlin"])
    sio.enter_room(sid, TOWER)


# ON ATTACK EVENT
@ sio.event
async def attack(sid, nickname):
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
    await sio.emit(MESSAGE_ATTACKED['message'], MESSAGE_ATTACKED, room=TOWER)
    sender.send(MESSAGE, ["Restlin"])


# ON DEFEND EVENT
@ sio.event
async def defend(sid, nickname):
    logger.log_info(f"DEFEND EVENT RAISED FROM USER {nickname}")
    MESSAGE['message'] = 'shield'
    MESSAGE['tower'] = TOWER
    MESSAGE['sender'] = nickname
    await sio.emit(MESSAGE['message'], room=TOWER)
    sender.send(MESSAGE, ['Restlin'])


# ON DISCONNECT EVENT
@ sio.event
async def disconnect(sid):
    logger.log_info(f"DISCONNECT EVENT RAISED WITH SID {sid}")
    MESSAGE['message'] = 'disconnect'
    MESSAGE['tower'] = TOWER
    MESSAGE['sender'] = sid
    sender.send(MESSAGE, ['Restlin'])
    sio.leave_room(sid, TOWER)


async def send_hu(message, content):
    await sio.emit(message, content, room=TOWER)


async def send_ha(message):
    await sio.emit(message, room=TOWER)


# DEFINING AMQP CONSUMER CALLBACK AND STARTING CONSUMER
def start_amqp(sio):

    print(f"Started amqp")

    def amqp_callback(ch, method, properties, body):
        message = json.loads(body)
        # on connected
        if(message['message'] == 'connect' or message['message'] == 'disconnect'):
            message['message'] = 'health_update'
            print(f"RISING USER DISCONNECTED WITH MESSAGE {message}")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(send_hu(message['message'], message))
            loop.close()
            logger.log_info(f"EMITTED INTERNALY {message['message']}")
        # on atacked
        elif(message['message'] == 'attack'):
            message['message'] = 'health_attacked'
            message['tower'] = TOWER
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(send_ha(message['message']))
            loop.close()
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

            message['shield'] = 0
            # SET SHIELD OF NEW MESSAGE TO BE 0 BECAUSE ON RESPONSE WE DON'T ATTACKER TO KNOW OUR SHIELD
            ch.basic_publish(exchange="Rabbit", routing_key=routing_key,
                             properties=pika.BasicProperties(
                                 correlation_id=properties.correlation_id),
                             body=json.dumps(message))
            logger.log_info(f"EMITTED INTERNALY {message['message']}")

    amqp__ini__(routing_key=TOWER, amqp_callback=amqp_callback)


def start_unicorn(_app, _port):
    uvicorn.run(_app, host='localhost', port=_port)


if __name__ == '__main__':
    try:
        PORT = int(sys.argv[1])
        logger = Logger(filename=f"tower{PORT}.log")
        TOWER = "Hocus" if PORT == 666 else "Pocus"
        amqp = threading.Thread(target=start_amqp, args=(sio,))
        amqp.start()
        uvicorn.run(app, host='localhost', port=PORT, log_level='error')
    except KeyboardInterrupt:
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
