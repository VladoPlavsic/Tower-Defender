import pika
import sys
import logging
import json

EXCHANGE_TYPE = 'topic'
EXCHANGE_NAME = 'Rabbit'
HOST = 'localhost'


def amqp__ini__(routing_key, amqp_callback=None):
    AMQP = pika.BlockingConnection(
        pika.ConnectionParameters(host=HOST))
    AMQP_CHANNEL = AMQP.channel()

    AMQP_CHANNEL.exchange_declare(
        exchange=EXCHANGE_NAME, exchange_type=EXCHANGE_TYPE)

    QUEUE = AMQP_CHANNEL.queue_declare(queue='', exclusive=True)

    QUEUE_NAME = QUEUE.method.queue

    AMQP_CHANNEL.queue_bind(
        exchange=EXCHANGE_NAME, queue=QUEUE_NAME, routing_key=routing_key)

    if(amqp_callback == None):
        def amqp_callback(ch, method, properties, body):
            print("Default callback, you should make custom!")

    AMQP_CHANNEL.basic_consume(
        queue=QUEUE_NAME, on_message_callback=amqp_callback)

    AMQP_CHANNEL.start_consuming()
