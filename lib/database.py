import os
import sqlite3
import typing

from.user import User

def seedDB(conn: sqlite3.Connection):
	"""
	Seeds the given database connection with a basic chat-server schema
	"""
	conn.execute('''CREATE TABLE user (username text primary key, email text, password text NOT NULL)''')
	conn.commit()

def getDB(path:str) -> sqlite3.Connection:
	"""
	Connects to the database at 'path'. If it doesn't already exist,
	one will be created and then populated with the chat-server schema.
	"""
	if os.path.isfile(path):
		return sqlite3.connect(path)
	
	if not os.path.isdir(os.path.dirname(path)):
		os.makedirs(os.path.dirname(path))

	conn = sqlite3.connect(path)
	seedDB(conn)
	return conn

def getUser(cur: sqlite3.Cursor, name: str) -> typing.Optional[User]:
	"""
	Gets the user named 'name' from the database as a (username, email) pair, or
	None if no such user was found.
	"""
	cur.execute('''SELECT username, email FROM user WHERE username=?''', (name,))
	u = cur.fetchone()
	if u is None:
		return None
	
	ret: User = (u[0], u[1])
	return ret

def createUser(cur: sqlite3.Cursor, u: User):
	"""
	Creates the passed user.
	"""
	if u.password is None:
		raise ValueError("Cannot create a user with no password")
	cur.execute('''INSERT INTO user (username, email, password) VALUES (?,?,?)''', (u.username, u.email, u.password))


class Database:
	"""Abstracts database operations for the chat server. Always expects a postgresql server with user 'chat' having read/write permissions for rows in 'Message' table."""

	def __init__(self, dbname):
		"""Initializes database connection with the database named 'dbname'."""
		# self.connection = psycopg2.connect("dbname="+dbname+" user=chat")

	def getMessages(self):
		"""Fetches messages from the server (currently all messages)"""
		# try:
		# 	cursor = self.connection.cursor()
		# 	cursor.execute('''SELECT * from message;''')
		# 	return cursor.fetchall()
		# except Exception as e:
		# 	print("[E] Database read error -")
		# 	print("\t"+str(e))
		# 	raise e
		# finally:
		# 	cursor.close()

	def storeMessage(self, msg):
		"""Stores a message on the server."""
		# try:
		# 	cursor = self.connection.cursor()
		# 	cursor.execute('''INSERT INTO message VALUES (%s, %s, %s)''', (msg.nickName, msg.date, msg.text))
		# 	self.connection.commit()
		# except Exception as e:
		# 	print("[E] Database write error (originating from user at "+msg.IP+") -")
		# 	print("\t"+str(e))
		# 	raise e
		# finally:
		# 	cursor.close()

