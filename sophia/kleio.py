'''
The Kleio module defines classes for process management.
'''

from multiprocessing import Pipe

class proxy: # Base proxy object

	def __init__(self, routine):
		
		self.calls, routine.calls = Pipe() # Pipe for function calls; should only contain one value at any given time
		self.messages, routine.messages = Pipe() # Pipe for message receiving
		self.result = None # Return value of task
		self.requests = [] # Tasks awaiting the return value of the key task
		self.references = [] # Tasks that this task references
		self.count = 0 # Reference counter

class reference: # Reference to proxy

	def __init__(self, routine):

		self.pid = routine.pid
		self.name = routine.name
		self.type = routine.type
		self.event = routine.start.message.type if type(routine.start).__name__ == 'event_statement' else None

	def __str__(self): return 'process ' + self.name