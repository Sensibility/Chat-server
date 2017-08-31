#!/usr/bin/env python3

import asyncio
import websockets
from logging import getLogger, INFO, StreamHandler
from message import Message

logger = getLogger('websockets')
logger.setLevel(INFO)
logger.addHandler(StreamHandler())

clients = dict()

async def relay(websocket):
	"""This function waits for messages from every connected client
	('websocket' is one client connection and the function is called asynchronously for each client)
	and forwards them to all other clients."""
	while True:
		message = await websocket.recv()
		print("recieved message from "+websocket.remote_address[0]+": "+message)
		message = Message(message, (websocket.remote_address[0], "Unkown"))
		if message.type == "login":
			clients[websocket.remote_address[0]][1] = message.text		
		elif message.type == "textmsg":
			message.nickName = clients[message.IP][1]
			for client in clients.values():
				await client[0].send(message.json())
		else:
			print("[W] Malformed message recieved from "+websocket.remote_address[0])


async def handler(websocket, path):
	"""This is called when a client connects to the server.
	'websocket' is a socket object generated for us that is connected to the client, and 'path' is the client's socket request path.
	This function handles keeping track of clients' connections and disconnections and passes messages off to 'relay()'"""
	global clients
	if websocket.remote_address[0] not in clients:
		clients[websocket.remote_address[0]] = [websocket, "Unkown"]
		print("[I] Added a new client - "+websocket.remote_address[0])
		print("[I] Dumping client list: ")
		for client in clients.keys():
			print("\t"+str(client))
	try:
		producer_task = asyncio.ensure_future(relay(websocket))
		done, pending = await asyncio.wait(
			[producer_task],
			return_when=asyncio.FIRST_COMPLETED,
		)

		for task in pending:
			task.cancel()
	finally:
		print("[I] User disconnected from "+websocket.remote_address[0])
		if not clients.pop(websocket.remote_address[0], False):
			print("[W] Disconnection from unregistered address - something wicked happened...")

start_server = websockets.serve(handler, host='', port=6969)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
