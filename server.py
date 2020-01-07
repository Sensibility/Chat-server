#!/usr/bin/env python3

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from os import path as ospath
from pathlib import Path
from sqlite3 import Connection, Cursor
import sys
import typing
import uuid
# from message import Message
# from database import Database
from lib import auth
from lib.database import getDB
from lib.error import Error, ErrorCode

class Client:
	"""
	Represents a client session connected to the chat server.
	"""
	authenticated = False
	addr: str
	def __init__(self, addr: str):
		self.addr = addr

clients:typing.Dict[str, Client] = {}

#Open a database connection
# try:
# 	db = Database("chat")
# except Exception as e:
# 	print("[E] Connection to database failed -")
# 	print("\t"+str(e))
# 	print("[W] Continuing without database...")
# 	db = False

__version__ = "0.0.1"

HOST: str
DB: Connection

class Handler(BaseHTTPRequestHandler):
	"""
	The handler for HTTP requests to the chat server. This aims for compliance with Matrix r0.6.0
	"""
	server_version = f"chat-server/{__version__}"
	protocol_version = "HTTP/1.1"
	error_content_type = "application/json"
	error_message_format = '{"error": "%(explain)s", "errcode": "%(message)s"}\n'
	_body: str = None
	_parsedBody: object = None
	cursor: Cursor

	def do_GET(self):
		"""
		Handles GET requests using the routes configured in self.routes["GET"].
		"""
		self.cursor = DB.cursor()
		try:
			self.routes["GET"].get(self.path, self.notFoundHandler)()
		except (Exception, KeyboardInterrupt) as e:
			print(sys.exc_info, file=sys.stderr)
			self.send_error(500, ErrorCode.UNKNOWN, e)
		finally:
			self.cursor.close()

	def do_POST(self):
		"""
		Handles POST requests using the routes configured in self.routes["POST"].
		"""
		self.cursor = DB.cursor()
		try:
			self.routes["POST"].get(self.path, self.notFoundHandler)()
		except (Exception, KeyboardInterrupt) as e:
			print(sys.exc_info, file=sys.stderr)
			self.send_error(500, ErrorCode.UNKNOWN, e)
		finally:
			self.cursor.close()

	def do_BREW(self):
		"""
		Handles BREW requests by informing the client that this server is a teapot, and cannot brew
		coffee.
		"""
		self.send_response(418, "I'm a teapot")
		self.end_headers()

	def authenticated(self) -> bool:
		"""
		Returns whether or not the client request was authenticated.
		"""
		try:
			return clients[self.parsedBody["session"]].authenticated
		except (ValueError, KeyError):
			return False

	def authenticate(self) -> bool:
		"""
		Attempts to parse the request body as a supported authentication flow. If it is a supported
		authentication flow, then it will attempt to perform authentication. Returns whether or not
		authentication was successful. If authentication *did* fail, this method will have already
		returned the appropriate error response, and so the caller doesn't need to do anything.
		"""
		try:
			body = self.parsedBody
		except json.JSONDecodeError as e:
			self.send_error(400, str(ErrorCode.NOT_JSON), f"Invalid JSON: {e.msg}")
			return False
		except ValueError as e:
			self.send_error(400, str(ErrorCode.UNKNOWN), f"Failed to read request body: {e}")
			return False

		try:
			authenticated = auth.authenticate(body, self.cursor)
		except Exception:
			self.unauthorizedHandler()
			return False

		if not authenticated:
			self.unauthorizedHandler()
			return False

		client = Client(f"{self.client_address[0]}:{self.client_address[1]}")
		client.authenticated = True
		clients[body["session"]] = client
		return True

	@property
	def body(self) -> str:
		"""
		The request body - unparsed. For a JSON-parsed body, use parsedBody.
		:raises: ValueError when reading the body fails
		"""
		if self._body is None:
			if "Content-Length" in self.headers:
				self._body = self.rfile.read(int(self.headers["Content-Length"]))
			elif "Transfer-Encoding" in self.headers and self.headers["Transfer-Encoding"].lower().strip() == "chunked":
				chunklength = int(self.rfile.read(3).rstrip("\r\n"))
				self._body = ""
				while chunklength >= 0:
					s = bytearray(chunklength)
					amt = self.rfile.readinto(s)
					if amt != chunklength:
						raise ValueError("Request contained invalid chunked content")
					self._body += s.decode()
					chunklength = int(self.rfile.read(4).strip("\r\n"))
			else:
				#Assume no body
				self._body = ""
		return self._body

	@property
	def parsedBody(self) -> object:
		"""
		The object obtained by parsing the request body as JSON.
		:raises: ValueError when reading or decoding the body fails.
		"""
		if self._parsedBody is None:
			self._parsedBody = json.loads(self.body)
		return self._parsedBody

	@property
	def routes(self) -> typing.Dict[str, typing.Dict[str, typing.Callable]]:
		"""
		A mapping of request methods to mappings of request paths to handler methods.
		"""
		return {
			"GET": {
				"/_matrix/client/versions": self._matrixVersions,
				"/.well-known/matrix/client": self._wellKnown,
				"/fakeEndpoint": self._fakeEndpoint,
			},
			"POST": {
				"/_matrix/client/r0/register": self._register
			}
		}

	def _fakeEndpoint(self):
		print("Handling fake endpoint")
		if not self.authenticated():
			print("unauthenticated, attempting to authenticate")
			if not self.authenticate():
				print("authentication failed")
				return

		self.success(b'"authenticated"')

	@property
	def homeserverBaseURL(self) -> str:
		"""
		The home server base_url property which is based on the -H/--host option. Specifically, it's
		set by the global HOST variable.
		"""
		return f'http://matrix.{HOST}'

	@property
	def identityserverBasURL(self) -> str:
		"""
		The identity server base_url property which is based on the -H/--host option. Specifically,
		it's set by the global HOST variable.
		"""
		return f'http://identity.{HOST}'

	def success(self, body: bytes):
		"""
		Sends a 200 OK success response with the given body. Sets the Content-Type to
		application/json, and automatically sets the Content-Length as is appropriate.
		"""
		self.send_response(200, "OK")
		self.send_header("Content-Type", "application/json")
		self.send_header("Content-Length", str(len(body)))
		self.end_headers()
		self.wfile.write(body)

	def _matrixVersions(self):
		self.success(b'{"versions":["r0.6.0"]}')

	def _wellKnown(self):
		resp = f'{{"m.homeserver":{{"base_url":"{self.homeserverBaseURL}"}},"m.identity_server":{{"base_url":"{self.identityserverBasURL}"}}}}\n'
		self.success(resp.encode())

	def _register(self):
		try:
			userData, err = auth.register(self.parsedBody, self.cursor, HOST)
		except json.JSONDecodeError as e:
			self.send_error(400, ErrorCode.BAD_JSON, f"Invalid JSON: {e.msg}")
		except ValueError as e:
			self.send_error(400, str(ErrorCode.UNKNOWN), f"Failed to read request body: {e}")
		
		if err is not None:
			self.send_error(400, str(err.code), err.error)
		else:
			self.success(json.dumps({"user_id": userData[0], "access_token": userData[1], "device_id": userData[2]}).encode() + b'\n')

	def notFoundHandler(self):
		"""
		Sends a 404 Not Found response with a Matrix-compliant JSON error object body.
		"""
		self.send_response(404, "Not Found")
		self.send_header("Content-Type", "application/json")
		err = Error("No resource was found for this request", ErrorCode.NOT_FOUND)
		response = str(err).encode() + b'\n'
		self.send_header("Content-Length", str(len(response)))
		self.end_headers()
		self.wfile.write(response)

	def unauthorizedHandler(self):
		"""
		Sends a 401 Unauthorized response with a Matrix-compliant JSON error object body.
		"""
		self.send_response(401, "Unauthorized")
		self.send_header("Content-Type:", "application/json")
		response = auth.renderFlows(session=str(uuid.uuid5(uuid.NAMESPACE_URL, self.homeserverBaseURL)))
		self.send_header("Content-Length", str(len(response)))
		self.end_headers()
		self.wfile.write(response)

def main() -> int:
	"""
	Runs the main logic of the server.
	Returns an exit code.
	"""
	global HOST
	global DB

	parser = ArgumentParser(description="A simple, Matrix-compliant web server.", formatter_class=ArgumentDefaultsHelpFormatter)
	parser.add_argument("-p", "--port", type=int, default=6969, help="Set the port on which the server listens")
	parser.add_argument("-H", "--host", type=str, default="localhost", help="Set the host on which the server listens")
	parser.add_argument("-v", "--version", action="version", version=__version__)
	parser.add_argument("--salt", default="pepper", help="sets the salt to use for hashed passwords.")
	parser.add_argument("-d", "--database", type=str, default=ospath.join(str(Path.home()), ".chat", "chat.db"), help="Specify a path to a SQLite3 database to use. If the database doesn't exist, it will be created and seeded.")
	args = parser.parse_args()

	try:
		DB = getDB(args.database)
	except OSError as e:
		print(f"Failed to connect to database at {args.database}", file=sys.stderr)
		return 2

	HOST = args.host
	httpd = HTTPServer((args.host, args.port), Handler)
	print(f"starting server at http://{args.host}:{args.port}/")
	try:
		httpd.serve_forever()
	except Exception as e:
		print("Halting server:", e, file=sys.stderr)
		return 1
	except KeyboardInterrupt as e:
		print("Halting server", file=sys.stderr)
		return 1
	# idk how you get down here
	return 0

if __name__ == "__main__":
	sys.exit(main())
