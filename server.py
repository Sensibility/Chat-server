#!/usr/bin/env python3

import asyncio
import websockets
from logging import getLogger, INFO, StreamHandler

logger = getLogger('websockets')
logger.setLevel(INFO)
logger.addHandler(StreamHandler())

clients = set()

async def hello(websocket, path):
    message = await websocket.recv()
    print("Recieved message: "+repr(message))

    greeting = "Message Recieved"
    await websocket.send(greeting)
    print("Sent confirmation of message recipt.")

async def handler(websocket, path):
	global clients
	clients.add(websocket)
	try:
		while True:
			await asyncio.wait([ws.send("Hello!") for ws in clients])
			await asyncio.sleep(10)
	finally:
		clients.remove(websocket)

start_server = websockets.serve(handler, host='', port=6969)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
