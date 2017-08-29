from json import loads, dumps
class Message:
	"""Represents a single message sent from a client"""
	def __init__(self, msg, client):
		self.IP = client[0]
		self.nickName = client[1]

		msg = json.loads(msg)
		try:
			self.type = msg["type"]
			self.text = msg["text"]
			self.date = msg["date"]
		except Exception as e:
			print(e)
			self.type = "error"
			self.text = str(e)
			self.date = "Now-ish"

	def str(self):
		return "Sent from "+self.IP+" ("+self.nickName+"):\n{\n\ttype: "+self.type+"\n\ttext: '"+self.text+"'\n\tdate: "+self.date+"\n}"


		