from multiprocessing import Pipe, current_process

class proxy: # Base proxy object

	def __init__(self, stream):
		
		self.bound = False
		self.stream = Pipe() # Pipe for message sending
		self.messages = Pipe() # Pipe for message receiving

class reference: # Reference to proxy

	def __init__(self, pid):

		self.pid = pid

	def send(self, value): # Proxy method to send to process

		current_process().namespace[self.pid].messages.send(value)

	def get(self): # Proxy method to get return value from process
		
		return current_process().namespace[self.pid].end.recv()

def initialise(stream):
	
	current_process().stream = stream