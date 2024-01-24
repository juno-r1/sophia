from cProfile import Profile
from re import match
from sys import stdin, stdout, stderr
from typing import Any

from .datatypes import iris
from .internal.presets import ERRORS, FLAGS, REGEX_NAMESPACE

streams = [ # Standard streams
	stdin,
	stdout,
	stderr
]

class handler:
	"""
	Error handler class.
	Stores information about the state of the program and the source file
	and performs a clean exit when an error is thrown.
	"""
	def __init__(
		self,
		source: str,
		flags: tuple[str, ...]
		) -> None:
		
		self.source = source
		self.flags = flags
		self.lock = False # Locks program execution
		self.profiler = None # Profiles are created within their tasks
		for flag in flags:
			if flag not in FLAGS:
				self.error('FLAG', flag) # Complete __init__ before potential exception

	def read(
		self,
		reference: iris.reference,
		message: str = ''
		) -> str:

		return input(message)

	def write(
		self,
		reference: iris.reference,
		message: str
		) -> str:

		print(message, sep = '', file = streams[reference.pid])
		return message

	def debug_initial(
		self,
		task,
		) -> None:
		"""
		Execute pre-runtime flags.
		"""
		if 'profile' in self.flags:
			self.profiler = Profile()
			self.profiler.enable()

	def debug_final(
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
			return task.call() # Return mutable state to supervisor

	def debug_processor( # Processor flags
		self,
		task
		) -> None:

		if 'processor' in self.flags:
			self.debug_instructions(task)

	def debug_instructions(
		self,
		task
		) -> None:
		"""
		Prints the calling environment's instructions.
		"""
		print('===', file = stderr)
		for i, instruction in enumerate(task.instructions):
			print(
                i,
				instruction,
				sep = '\t',
				file = stderr
            )
		print('===', file = stderr)

	def debug_namespace(
		self,
		task
		) -> None:
		"""
		Prints the user-accessible namespace.
		"""
		print(
            '===',
			task.name,
			'---',
			'\n---\n'.join(('{0} {1} {2}'.format(
				name,
				task.types[name],
				value) for name, value in task.values.items() if match(REGEX_NAMESPACE, name))
			),
			'===',
			sep = '\n',
			file = stderr
        )

	def debug_supervisor(
		self,
		message
		) -> None:
		"""
		Prints the current message in the supervisor.
		"""
		print(message, file = stderr)

	def debug_task(
		self,
		task
		) -> None:
		"""
		Prints the current instruction and subroutine.
		"""
		print(
            str(task.path),
			task.op,
			sep = '\t',
			file = stderr
        )

	def timeout(
		self
		) -> None:
		"""
		Prints a timeout warning.
		"""
		print(
            '===',
			'Timeout warning',
			'Enter Ctrl+C to interrupt program',
			'===',
			sep = '\n',
			file = stderr
        )

	def error(
		self,
		status: str,
		*args: tuple
		) -> None:
		"""
		Throws an error and terminates the current task.
		"""
		if 'suppress' not in self.flags:
			print(
                '===',
				#'{0} (line {1})'.format(self.name, self.op.line),
				ERRORS[status].format(*args) if args else ERRORS[status],
				'===',
				sep = '\n',
				file = stderr
            )
		self.lock = True
		raise SystemExit
