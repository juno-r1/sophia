from multiprocessing import Pipe, current_process

class proxy: # Base proxy object

	def __init__(self, routine):
		
		self.calls, routine.calls = Pipe() # Pipe for function calls; should only contain one value at any given time
		self.messages, routine.messages = Pipe() # Pipe for message receiving
		self.result = None # Return value of task
		self.requests = [] # Tasks awaiting the return value of the key task
		self.references = [] # Tasks with a reference to this task; functions as a reference counter

class reference: # Reference to proxy

	def __init__(self, pid):

		self.pid = pid

def initialise(stream):
	
	current_process().stream = stream