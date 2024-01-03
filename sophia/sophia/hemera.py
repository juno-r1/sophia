from cProfile import Profile
from re import match
from sys import stderr
from typing import Any

from .internal.presets import ERRORS, TOKENS_NAMESPACE

class handler:
	"""
	Error handler class.
	Stores information about the current state of the program,
	and performs a clean exit when an error is thrown.
	"""
	def __init__(
		self,
		*flags: tuple[str, ...]
		) -> None:
		
		self.flags = flags
		self.throw = True
		self.profiler = Profile()

	def initial( # Initial flags
		self,
		task,
		) -> None:
		"""
		Execute pre-runtime flags.
		"""
		if 'instructions' in self.flags:
			self.debug_instructions(task)
		if 'profile' in self.flags:
			self.profiler.enable()

	def final( # Final flags
		self,
		task,
		value: Any
		) -> None:
		"""
		Execute post-runtime flags and terminate runtime loop.
		"""
		if 'profile' in self.flags:
			self.profiler.disable()
			self.profiler.print_stats(sort = 'cumtime')
		if 'namespace' in self.flags:
			self.debug_namespace(task)
		if 'debug' in self.flags:
			return value
		else:
			task.message('terminate')
			return task.state() # Return mutable state to supervisor

	def debug_instructions(
		self,
		task
		) -> None:
		"""
		Prints the calling environment's instructions.
		"""
		print('===', file = stderr)
		for i, instruction in enumerate(task.instructions):
			print(i,
				  instruction,
				  sep = '\t',
				  file = stderr)
		print('===', file = stderr)

	def debug_namespace(
		self,
		task
		) -> None:
		"""
		Prints the user-accessible namespace.
		"""
		print('===',
			  task.name,
			  '---',
			  '\n---\n'.join(('{0} {1} {2}'.format(
				  name,
				  task.types[name],
				  value) for name, value in task.values.items() if match(TOKENS_NAMESPACE, name))
			  ),
			  '===',
			  sep = '\n',
			  file = stderr)

	def debug_task(
		self,
		task
		) -> None:
		"""
		Prints the current instruction.
		"""
		print(str(task.path),
			  task.op,
			  sep = '\t',
			  file = stderr)

	def runtime_error(
		self,
		status: str,
		*args: tuple
		) -> None:
		"""
		Throws an error and performs a system exit unless suppressed.
		"""
		if self.throw: # Suppresses error for assertions
			if 'suppress' not in self.flags:
				print('===',
					  '{0} (line {1})'.format(self.name, self.op.line),
					  ERRORS[status].format(*args) if args else ERRORS[status],
					  '===',
					  sep = '\n',
					  file = stderr)
			raise SystemExit