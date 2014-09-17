import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.autoreload
import pika
from pika import adapters

from sockjs.tornado import SockJSRouter, SockJSConnection

io_instance = None


def pre_autorelaod():
    print "Server is reloaded."


tornado.autoreload.add_reload_hook(pre_autorelaod)


class SimpleNotification(SockJSConnection):

    listening_nodes = set()

    def on_open(self, request):
        print "{} starts listening notification.".format(request.ip)
        print "Online node numbers: {}".format(len(self.listening_nodes))
        self.listening_nodes.add(self)
        self.ip = request.ip
        self.application = self.session.handler.application

        if not self.application.pika_client._sockjs:
            def ws_callback(conn):
                self.application.pika_client._sockjs = conn.result()
            tornado.websocket.websocket_connect(
                "ws://localhost:%s/notification/websocket" % self.application.port,
                callback=ws_callback)

    def on_message(self, msg):
        print "A message %s need to be handled." % msg
        self.broadcast(self.listening_nodes, msg)

    def on_close(self):
        print "{} stops listening notification.".format(self.ip)
        print "Online node numbers: {}".format(len(self.listening_nodes))
        self.listening_nodes.remove(self)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")


class SimplePikaClient(object):
    EXCHANGE = 'message'
    EXCHANGE_TYPE = 'direct'
    QUEUE = 'test'
    ROUTING_KEY = 'test'

    def __init__(self, amqp_url):
        self._connection = None
        self._channel = None
        self._sockjs = None
        # self._closing = False
        # self._consumer_tag = None
        self._url = amqp_url
        self._broadcast_queue = []
        self.connect()

    def connect(self):
        self._connection = adapters.TornadoConnection(pika.URLParameters(self._url),
                                                      self.on_connected)

    def on_connected(self, unused_connection):
        print "Connection Opened..."
        self._connection.channel(on_open_callback=self.on_channel_opened)

    def on_channel_opened(self, channel):
        print "Channel Opened..."
        self._channel = channel
        self._channel.exchange_declare(self.on_exchange_declared,
                                       self.EXCHANGE,
                                       self.EXCHANGE_TYPE)

    def on_exchange_declared(self, unused_frame):
        print "Exchange Declared."
        self._channel.queue_declare(self.on_queue_declared, self.QUEUE)

    def on_queue_declared(self, method_frame):
        print "Queue Declared."
        self._channel.queue_bind(self.on_binded, self.QUEUE,
                                 self.EXCHANGE, self.ROUTING_KEY)

    def on_binded(self, unused_frame):
        print "Channel Binded."
        self._channel.basic_consume(self.on_message, self.QUEUE)

    def on_message(self, unused_channel, basic_deliver, properties, body):
        """Broadcast incoming messages to all clients (browser)."""
        delivery_tag = basic_deliver.delivery_tag
        if self._sockjs:
            self._sockjs.write_message(body)
        # else:
        #     print "Socket connection is not ready. Put new message into local queue."
        #     self._broadcast_queue.append(body)
        self._channel.basic_ack(delivery_tag)


if __name__ == "__main__":

    io_instance = tornado.ioloop.IOLoop.instance()

    broadcast_router = SockJSRouter(SimpleNotification, '/notification')

    pika_client = SimplePikaClient("amqp://guest:guest@127.0.0.1/%2F")

    application = tornado.web.Application([
        (r"/", MainHandler),
    ] + broadcast_router.urls, debug=True, autoload=True)

    application.port = 9999
    application.pika_client = pika_client

    application.listen(application.port)
    io_instance.start()
