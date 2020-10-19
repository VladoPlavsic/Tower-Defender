import pika
import logging
import sys
import os
import json
import uuid


class Sender:

    __EXCHANGE_TYPE = 'topic'

    def __init__(self, host, exchange_name):
        self.__HOST = host
        self.__EXCHANGE_NAME = exchange_name

        self.__CONNECTION = self.__connect()
        self.__CHANNEL = self.__CONNECTION.channel()
        self.__RESPONSE = None

    # IF WE WANT ACK

    def create_consumer(self, routing_key):
        self.__create_exchange()
        result = self.__CHANNEL.queue_declare(queue='', exclusive=True)
        self.__CALLBACK_QUEUE = result.method.queue
        self.__CHANNEL.queue_bind(
            exchange=self.__EXCHANGE_NAME, queue=self.__CALLBACK_QUEUE, routing_key=routing_key)
        self.__CHANNEL.basic_consume(
            queue=self.__CALLBACK_QUEUE,
            on_message_callback=self.on_response,
            auto_ack=True)

    def on_response(self, ch, methid, props, body):
        if self.__CORR_ID == props.correlation_id:
            self.__RESPONSE = body

    def __connect(self):
        return pika.BlockingConnection(pika.ConnectionParameters(host=self.__HOST))

    def __create_exchange(self):
        self.__CHANNEL.exchange_declare(
            exchange=self.__EXCHANGE_NAME, exchange_type=self.__EXCHANGE_TYPE)

    def send(self, message, routing_key):
        for key in routing_key:
            self.__CHANNEL.basic_publish(exchange=self.__EXCHANGE_NAME,
                                         routing_key=key,
                                         body=json.dumps(message))

    def send_with_ack(self, message, routing_key):
        self.__CORR_ID = str(uuid.uuid4())
        self.__CHANNEL.basic_publish(exchange=self.__EXCHANGE_NAME,
                                     routing_key=routing_key,
                                     properties=pika.BasicProperties(
                                         reply_to=routing_key,
                                         correlation_id=self.__CORR_ID,
                                     ),
                                     body=json.dumps(message))
        while self.__RESPONSE is None:
            self.__CONNECTION.process_data_events()

        temp = self.__RESPONSE
        self.__RESPONSE = None

        return temp

    def _close_connection(self):
        self.__CONNECTION.close()


sender = Sender("localhost", "Rabbit")
