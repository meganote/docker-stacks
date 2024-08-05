# coding=utf-8

import asyncio
import base64
import json

from websockets.sync.client import connect


def hello():
    with connect("ws://ip:port") as websocket:
        data = dict(
            text="你好",
        )
        websocket.send(json.dumps(data))
        message = websocket.recv()
        data: dict = json.loads(message)
        audio = data.get("audio")
        b64data = base64.b64decode(audio)


hello()
