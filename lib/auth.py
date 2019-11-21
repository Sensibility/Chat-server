"""
This module defines authentication types and methods for completing authentication flows.
"""

import json
import typing

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

