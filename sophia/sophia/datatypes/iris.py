from dataclasses import dataclass
from multiprocessing import Pipe

#class proxy:
#	"""Proxy object for a task. Represents the state of a task in the supervisor."""
#	def __init__(self, routine):
		
#		self.calls, routine.calls = Pipe() # Pipe for function calls; should only contain one value at any given time
#		self.messages, routine.messages = Pipe() # Pipe for message receiving
#		self.result = None # Return value of task
#		self.state = None # Return state of task
#		self.requests = [] # Tasks awaiting the return value of the key task
#		self.references = [] # Tasks that this task references
#		self.count = 0 # Reference counter

@dataclass(slots = True, repr = False)
class reference:
	"""Reference object for a proxy. Represents the user-accessible state of a task."""
	name: str = ''
	pid: int = 0
	check: str = 'untyped'

	def __str__(self) -> str: return '{0}:{1}'.format(self.name, self.pid)

	__repr__ = __str__

"""
Standard streams and I/O operations.
These streams are abstract interfaces with stdin, stdout, and stderr.
Their PIDs correspond to their Unix file descriptors.
"""

std_stdin = reference('stdin', 0)
std_stdout = reference('stdout', 1)
std_stderr = reference('stderr', 2)