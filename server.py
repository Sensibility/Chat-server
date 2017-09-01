#!/usr/bin/env python3

import asyncio
import websockets
from logging import getLogger, INFO, StreamHandler
from message import Message
from database import Database

logger = getLogger('websockets')
logger.setLevel(INFO)
logger.addHandler(StreamHandler())

clients = dict()

#Open a database connection
try:
	db = Database("chat")
except Exception as e:
	print("[E] Connection to database failed -")
	print("\t"+str(e))
	print("[W] Continuing without database...")
	db = False


async def relay(websocket):
	"""This function waits for messages from every connected client
	('websocket' is one client connection and the function is called asynchronously for each client)
	and forwards them to all other clients."""
	global db
	while True:

		#first wait for a message
		message = await websocket.recv()
		addr = websocket.remote_address[0]
		username = clients[addr][1]
		print("[I] Recieved message from "+addr+" ("+username+")")

		#If it's binary data, it's probably a voip packet, so try that
		if isinstance(message, bytes):
			print("it was a voip packet!")

		#... but if it's a string it's either login info or a text message
		elif isinstance(message, str):
			message = Message(message, (addr, username))

			#if it's a login message, store their nickname for later and send them some messages they might've missed.
			if message.type == "login":
				
				clients[websocket.remote_address[0]][1] = message.text

				#send messages to 'em if the database was connected to successfully
				if db:
					try:
						for msg in db.getMessages():
							await websocket.send(Message.jsonify(("sender", "date", "text"), msg))
					except Exception as e:
						del db
						db = False


			#if it's a  text message, store it to the database and send it to everyone else
			elif message.type == "textmsg":
				for client in clients.values():
					await client[0].send(message.json())
				if db:
					try:
						db.storeMessage(message)
					except Exception as e:
						del db
						db = False
			else:
				print("[W] Malformed message recieved from "+addr)
		else:
			print("[E] Unknown error occured during message receipt from "+addr)


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
	except:
		print("[I] User disconnected from "+websocket.remote_address[0])
	finally:
		if not clients.pop(websocket.remote_address[0], False):
			print("[W] Disconnection from unregistered address - something wicked happened...")

start_server = websockets.serve(handler, host='', port=6969)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
