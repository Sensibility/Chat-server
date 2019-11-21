"""
This module defines the Matrix error spec for returning error messages
"""

import typing
from enum import Enum

class ErrorCode(Enum):
	# Common error codes
	FORBIDDEN = "M_FORBIDDEN"
	UNKNOWN_TOKEN = "M_UNKNOWN_TOKEN"
	MISSING_TOKEN = "M_MISSING_TOKEN"
	BAD_JSON = "M_BAD_JSON"
	NOT_JSON = "M_NOT_JSON"
	NOT_FOUND = "M_NOT_FOUND"
	LIMIT_EXCEEDED = "M_LIMIT_EXCEEDED"
	UNKNOWN = "M_UNKNOWN"

	# less common error codes
	UNRECOGNIZED = "M_UNRECOGNIZED"
	UNAUTHORIZED = "M_UNAUTHORIZED"
	USER_DEACTIVATED = "M_USER_DEACTIVATED"
	USER_IN_USE = "M_USER_IN_USE"
	INVALID_USERNAME = "M_INVALID_USERNAME"
	ROOM_IN_USE = "M_ROOM_IN_USE"
	INVALID_ROOM_STATE = "M_INVALID_ROOM_STATE"
	THREEPID_IN_USE = "M_THREEPID_IN_USE"
	THREEPID_NOT_FOUND = "M_THREEPID_NOT_FOUND"
	THREEPID_AUTH_FAILED = "M_THREEPID_AUTH_FAILED"
	THREEPID_DENIED = "M_THREEPID_DENIED"
	SERVER_NOT_TRUSTED = "M_SERVER_NOT_TRUSTED"
	UNSUPPORTED_ROOM_VERSION = "M_UNSUPPORTED_ROOM_VERSION"
	INCOMPATIBLE_ROOM_VERSION = "M_INCOMPATIBLE_ROOM_VERSION"
	BAD_STATE = "M_BAD_STATE"
	GUEST_ACCESS_FORBIDDEN = "M_GUEST_ACCESS_FORBIDDEN"
	CAPTCHA_NEEDED = "M_CAPTCHA_NEEDED"
	CAPTCHA_INVALID = "M_CAPTCHA_INVALID"
	MISSING_PARAM = "M_MISSING_PARAM"
	TOO_LARGE = "M_TOO_LARGE"
	EXCLUSIVE = "M_EXCLUSIVE"
	RESOURCE_LIMIT_EXCEEDED = "M_RESOURCE_LIMIT_EXCEEDED"
	CANNOT_LEAVE_SERVER_NOTICE_ROOM = "M_CANNOT_LEAVE_SERVER_NOTICE_ROOM"

class Error:
	code: ErrorCode
	error: str
	roomVersion: typing.Optional[str]
	adminContact: typing.Optional[str]

	def __init__(self, error: str, errCode: ErrorCode = ErrorCode.UNKNOWN, *, roomVersion: str = None, adminContact: str = None):
		self.error = error
		self.roomVersion = roomVersion
		if errCode == ErrorCode.RESOURCE_LIMIT_EXCEEDED and not adminContact:
			raise ValueError("RESOURCE_LIMIT_EXCEEDED must provide adminContact")
		self.code = errCode
		self.adminContact = adminContact

	def __str__(self) -> str:
		"""
		Implements str(Error) by rendering it as a JSON string
		"""
		if self.code == ErrorCode.INCOMPATIBLE_ROOM_VERSION and self.roomVersion:
			return f'{{"errcode": "{self.code.value}", "error": "{self.error}", "room_version": "{self.roomVersion}"}}'
		if self.code == ErrorCode.RESOURCE_LIMIT_EXCEEDED:
			return f'{{"errcode": "{self.code.value}", "error": "{self.error}", "admin_contact": "{self.adminContact}"}}'
		return f'{{"errcode": "{self.code.value}", "error": "{self.error}"}}'

	def __repr__(self) -> str:
		"""
		Implements repr(Error)
		"""
		return f'Error(error={self.error!r}, errCode={self.code!r})'
