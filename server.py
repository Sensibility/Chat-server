#!/usr/bin/env python3

import asyncio
import websockets
from logging import getLogger, INFO, StreamHandler
from message import Message

logger = getLogger('websockets')
logger.setLevel(INFO)
logger.addHandler(StreamHandler())

clients = set()

async def receive(websocket):
	pass

async def relay(websocket):
	while True:
		print(websocket.__dict__)

async def handler(websocket, path):
	global clients
	clients.add(websocket)
	try:
		await asyncio.wait([ws.send("Hello!") for ws in clients])
		#consumer_task = asyncio.ensure_future(receive(websocket))
		producer_task = asyncio.ensure_future(relay(websocket))
		done, pending = await asyncio.wait(
			[consumer_task, producer_task],
			return_when=asyncio.FIRST_COMPLETED,
		)

		for task in pending:
			task.cancel()
	finally:
		clients.remove(websocket)

start_server = websockets.serve(handler, host='', port=6969)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
