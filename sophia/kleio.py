from multiprocessing import Pipe

class proxy: # Base proxy object

	def __init__(self, process):
		
		self.bound = False # Determines whether process is bound
		self.messages, process.messages = Pipe() # Pipe to send messages
		self.end, process.end = Pipe() # Pipe for return value

class reference: # Reference to proxy

	def __init__(self, pid):

		self.pid = pid

	def send(self, value): # Proxy method to send to process

		return self.messages.send(value)

	def get(self): # Proxy method to get return value from process

		return self.end.recv()