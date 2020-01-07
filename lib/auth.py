"""
This module defines authentication types and methods for completing authentication flows.
"""
from enum import Enum
import hashlib
import json
from sqlite3 import Cursor
import typing
import uuid

from .error import Error, ErrorCode
from .database import createUser
from .user import User

class Flow:
	"""
	A Flow is a single authentication flow.
	"""
	stages: typing.List[str]
	params: typing.Dict[str, typing.Any]

	def __init__(self, stages:typing.List[str], params:typing.Dict[str, typing.Any] = None):
		self.stages = stages
		self.params = params


#: flows is a list of acceptable, supported authentication flows.
flows = [Flow(["m.login.password"])]


def renderFlows(*, completed:typing.List[str] = None, session:str = None) -> bytes:
	"""
	Renders the allowed authentication flows into a JSON payload.
	:param completed: If given, this will set the auth flow stages that the user has completed.
	:param session: If given, adds a session string that clients are required to present with their
		requests.
	"""
	obj = {"flows": []}
	for f in flows:
		obj["flows"].append({"stages": f.stages})
		if f.params:
			if "params" not in obj:
				obj["params"] = f.params
			else:
				for p,v in f.params:
					obj["params"][p] = v

	if completed:
		obj["completed"] = completed
	if session:
		obj["session"] = session

	return json.dumps(obj).encode() + b'\n'

AuthenticationData = typing.NamedTuple("AuthenticationData", Type=str, session=str)

SALT = b'salt'  # ¯\_(ツ)_/¯

class RegistrationRequest:
	kind: str
	inhibitLogin: bool
	auth: AuthenticationData
	username: str
	password: str
	deviceID: str

	def __init__(self, **kwargs):
		self.kind = kwargs.get("kind", "user")
		if not isinstance(self.kind, str):
			raise TypeError("'kind' must be a string")
		elif self.kind not in {"user", "guest"}:
			raise ValueError("'kind' must be 'user' or 'guest'")

		self.inhibitLogin = kwargs.get("inhibitLogin", False)
		if not isinstance(self.inhibitLogin, bool):
			raise TypeError("'inhibit_login' must be a boolean")

		if "username" not in kwargs:
			raise ValueError("'username' is required")
		if not isinstance(kwargs["username"], str):
			raise TypeError("'username' must be a string")
		self.username = kwargs["username"]

		if "password" not in kwargs:
			raise ValueError("'password' is required")
		if not isinstance(kwargs["password"], str):
			raise TypeError("'password' must be a string")
		self.password = kwargs["password"]

		self.deviceID = kwargs.get("device_id", str(uuid.uuid4()))
		if not isinstance(self.deviceID, str):
			raise TypeError("'device_id' must be a string")

		if "auth" not in kwargs:
			raise ValueError("'auth' is required")
		try:
			self.auth = AuthenticationData(kwargs["auth"]["type"], kwargs["auth"]["session"])
		except (TypeError, ValueError, KeyError):
			raise TypeError("'auth' key must have 'type' and 'session'")

	def user(self) -> User:
		"""
		Generates a User from this request. Their password is hashed.
		"""
		passwd = hashlib.pbkdf2_hmac('sha256', self.password.encode(), SALT, 1000000)
		return User(self.username, passwd)

def register(req: dict, db: Cursor, host: str) -> typing.Tuple[typing.Tuple[str, str, str], typing.Optional[Error]]:
	"""
	Parses the passed request as a user registration request object, and registers the user.
	'host' must be the server's domain, for generating a userID
	"""
	try:
		registrationRequest = RegistrationRequest(**req)
	except (ValueError, TypeError) as e:
		return None, Error(str(e), ErrorCode.BAD_JSON)

	if registrationRequest.kind == "guest":
		# TODO make guests work
		return None, Error("This server doesn't support guest accounts", ErrorCode.GUEST_ACCESS_FORBIDDEN)
	if registrationRequest.kind != "user":
		return None, Error("'kind' must be one of 'user' or 'guest'", ErrorCode.BAD_JSON)

	user = registrationRequest.user()
	userID = f"@{user.username}:{host}"

	createUser(db, user)

	return (userID, "fake Auth token", registrationRequest.deviceID), None

def authenticate(req: dict, db: Cursor) -> bool:
	"""
	Attempts to authenticate a user based on their request
	"""
	return True
