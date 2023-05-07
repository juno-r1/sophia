'''
The Kleio module defines classes for process management.
'''

from multiprocessing import Pipe

class proxy:
	"""Proxy object for a task. Represents the state of a task in the supervisor."""
	def __init__(self, routine):
		
		self.calls, routine.calls = Pipe() # Pipe for function calls; should only contain one value at any given time
		self.messages, routine.messages = Pipe() # Pipe for message receiving
		self.result = None # Return value of task
		self.state = None # Return state of task
		self.requests = [] # Tasks awaiting the return value of the key task
		self.references = [] # Tasks that this task references
		self.count = 0 # Reference counter

class reference:
	"""Reference object for a proxy. Represents the state of a task in another task."""
	__slots__ = ('name', 'type', 'pid', 'check')

	def __init__(self, routine, check = None):
		
		self.name = routine.name
		self.type = routine.type
		self.pid = routine.pid
		self.check = check