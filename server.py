#!/usr/bin/env python3

import asyncio
import websockets
from logging import getLogger, INFO, StreamHandler
from message import Message

logger = getLogger('websockets')
logger.setLevel(INFO)
logger.addHandler(StreamHandler())

clients = dict()

def IPtoStr(ip):
	string = ""
	for b in ip:
		string += str(b)
	return string

async def receive(websocket):
	pass

async def relay(websocket):
	while True:
		message = await websocket.recv()
		message = Message(message, (IPtoStr(websocket.remote_address), "Unkown"))
		if message.type == "login":
			clients[IPtoStr(websocket.remote_address)][1] = message.text
		message = Message(message.json(), (IPtoStr(websocket.remote_address), clients[IPtoStr(websocket.remote_address)]))
		
		if message.type == "textmsg":
			for client in clients.keys():
				if client != IPtoStr(websocket.remote_address):
					clients[client].send(message.json())


async def handler(websocket, path):
	global clients
	if IPtoStr(websocket.remote_address) not in clients:
		clients[IPtoStr(websocket.remote_address)] = [websocket, "Unkown"]
		print("[I] Added a new client - "+IPtoStr(websocket.remote_address))
		print("[I] Dumping client list: ")
		for client in clients.keys():
			print("\t"+str(client))
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
	except Exception as e:
		print(e)

start_server = websockets.serve(handler, host='', port=6969)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
