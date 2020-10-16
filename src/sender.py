import pika
import logging
import sys
import os
import json


class Sender:

    def __init__(self, host, exchange_name):
        self._HOST = host
        self._EXCHANGE_NAME = exchange_name
        self._EXCHANGE_TYPE = 'topic'

        self._CONNECTION = self._connect()
        self._CHANNEL = self._CONNECTION.channel()

        self._create_exchange()

    def _connect(self):
        return pika.BlockingConnection(pika.ConnectionParameters(host=self._HOST))

    def _create_exchange(self):
        self._CHANNEL.exchange_declare(
            exchange=self._EXCHANGE_NAME, exchange_type=self._EXCHANGE_TYPE)

    def _send(self, message, routing_key):
        for key in routing_key:
            self._CHANNEL.basic_publish(exchange=self._EXCHANGE_NAME,
                                        routing_key=key,
                                        body=json.dumps(message))

        print(f"[x] Sent {message}")

    def _close_connection(self):
        self._CONNECTION.close()


sender = Sender("localhost", "Rabbit")
