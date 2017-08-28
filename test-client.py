#!/usr/bin/env python3

import asyncio
import websockets

async def hello():
	async with websockets.connect('ws://127.0.0.1:6969') as websocket:
		await websocket.send("hello")
		print("Sent message: 'hello'")
		response = await websocket.recv()
		print("Recieved: "+repr(response))

asyncio.get_event_loop().run_until_complete(hello())
