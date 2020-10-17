import pika
import logging
import sys
import os
import json


class Sender:

    __EXCHANGE_TYPE = 'topic'

    def __init__(self, host, exchange_name):
        self.__HOST = host
        self.__EXCHANGE_NAME = exchange_name

        self.__CONNECTION = self.__connect()
        self.__CHANNEL = self.__CONNECTION.channel()

        self.__create_exchange()

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

    def _close_connection(self):
        self.__CONNECTION.close()


sender = Sender("localhost", "Rabbit")
