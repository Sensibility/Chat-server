#!/usr/bin/env python3

import asyncio
import websockets
from logging import getLogger, INFO, StreamHandler
from message import Message

logger = getLogger('websockets')
logger.setLevel(INFO)
logger.addHandler(StreamHandler())

clients = dict()

async def receive(websocket):
	pass

async def relay(websocket):
	while True:
		message = await websocket.recv()
		message = Message(message, (websocket.remote_address[0], "Unkown"))
		if message.type == "login":
			clients[websocket.remote_address[0]][1] = message.text
		message = Message(message.json(), (websocket.remote_address[0], clients[websocket.remote_address[0]]))
		
		if message.type == "textmsg":
			for client in clients.values():
				client.send(message.json())


async def handler(websocket, path):
	global clients
	if websocket.remote_address[0] not in clients:
		clients[websocket.remote_address[0]] = [websocket, "Unkown"]
		print("[I] Added a new client - "+websocket.remote_address[0])
		print("[I] Dumping client list: ")
		for client in clients.keys():
			print("\t"+str(client))
	try:
		await asyncio.wait([ws[0].send("Hello!") for ws in clients.values()])
		#consumer_task = asyncio.ensure_future(receive(websocket))
		producer_task = asyncio.ensure_future(relay(websocket))
		done, pending = await asyncio.wait(
			[producer_task],
			return_when=asyncio.FIRST_COMPLETED,
		)

		for task in pending:
			task.cancel()
	except Exception as e:
		print(e)

start_server = websockets.serve(handler, host='', port=6969)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
