from dataclasses import dataclass
from multiprocessing import Pipe
from sys import stdin, stdout, stderr
from typing import Any

class proxy:
	"""
	Proxy object for a task. Represents the state of a task in the supervisor.
	"""
	def __init__(self, task):
		
		self.calls, task.calls = Pipe() # Pipe for function calls; should only contain one value at any given time
		self.messages, task.messages = Pipe() # Pipe for message receiving
		self.result = None # Return value of task
		self.state = None # Return state of task
		self.requests = [] # Tasks awaiting the return value of the key task
		self.references = [] # Tasks that this task references
		self.count = 0 # Reference counter

@dataclass(slots = True, repr = False)
class reference:
	"""
	Reference object for a proxy. Represents the user-accessible state of a task.
	"""
	name: str
	pid: int
	check: Any = None # typedef
	readable: bool = False
	writeable: bool = False

	def __str__(self) -> str: return '{0}:{1}'.format(self.name, self.pid)

	__repr__ = __str__

@dataclass(slots = True, repr = False)
class message:
	"""
	Message object. Transmits information to and from the supervisor.
	"""
	pid: int
	instruction: str
	args: tuple

	def __str__(self) -> str: return '{0}: {1} {2}'.format(self.pid, self.instruction, ' '.join(str(i) for i in self.args))

"""
Standard streams and I/O operations.
These streams are abstract interfaces with stdin, stdout, and stderr.
Their PIDs correspond to their Unix file descriptors.
"""

std_stdin = reference('stdin', 0, readable = True)
std_stdout = reference('stdout', 1, writeable = True)
std_stderr = reference('stderr', 2, writeable = True)