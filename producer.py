#!/usr/bin/env python
import pika
import sys


def publish_message(exchange, exchange_type, body, routing_key=""):

    connection = pika.BlockingConnection(pika.URLParameters("amqp://guest:guest@localhost/%2F"))
    channel = connection.channel()

    channel.exchange_declare(exchange=exchange,
                             type=exchange_type)

    channel.queue_declare(queue='task_queue', exclusive=False)

    message = ' '.join(sys.argv[1:]) or "info: {}".format(body)
    channel.basic_publish(exchange=exchange,
                          routing_key=routing_key,
                          body=message)
    print " [x] Sent %r" % (message,)

    connection.close()
