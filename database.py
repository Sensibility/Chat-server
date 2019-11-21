import psycopg2

class Database:
	"""Abstracts database operations for the chat server. Always expects a postgresql server with user 'chat' having read/write permissions for rows in 'Message' table."""

	def __init__(self, dbname):
		"""Initializes database connection with the database named 'dbname'."""
		self.connection = psycopg2.connect("dbname="+dbname+" user=chat")

	def getMessages(self):
		"""Fetches messages from the server (currently all messages)"""
		try:
			cursor = self.connection.cursor()
			cursor.execute('''SELECT * from message;''')
			return cursor.fetchall()
		except Exception as e:
			print("[E] Database read error -")
			print("\t"+str(e))
			raise e
		finally:
			cursor.close()

	def storeMessage(self, msg):
		"""Stores a message on the server."""
		try:
			cursor = self.connection.cursor()
			cursor.execute('''INSERT INTO message VALUES (%s, %s, %s)''', (msg.nickName, msg.date, msg.text))
			self.connection.commit()
		except Exception as e:
			print("[E] Database write error (originating from user at "+msg.IP+") -")
			print("\t"+str(e))
			raise e
		finally:
			cursor.close()

