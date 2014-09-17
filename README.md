
# Python Simple PubSub

A simple message pub/sub by tornado, rabbitmq and websocket

## Prerequisite

1. python2.7+
2. python-pip
3. rabbitmq-server

## Installation

```
$ pip install -r requirements
```

## Run Server

```
$ python server.py
```

## Connect

Open a browser and input the following address: `http://localhost:9999`

## Work with message queue

By using `publish_message` function in `producer.py`, you can send a message to clients.

``` python
import producer
producer.publish_message("message", "direct", "My test message!!!", "test")
```

