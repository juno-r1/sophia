from sys import stderr

from .internal.presets import ERRORS

#def stream_in(value = ''): return input(value)

#def stream_out(value): print(value, sep = '')

#def stream_err(value): print(value, sep = '', file = stderr)

#"""
#Debug and error instructions.
#"""

#def debug_instructions(task):
	
#	print('===', file = stderr)
#	for i, instruction in enumerate(task.instructions):
#		print(i,
#			  instruction,
#			  sep = '\t',
#			  file = stderr)
#	print('===', file = stderr)

#def debug_namespace(task): # Takes a task object
	
#	print('===',
#	      task.name,
#		  '---',
#		  '\n---\n'.join((' '.join((name, str(task.types[name]), str(value))) for name, value in task.values.items() if name[0] not in '0123456789&')),
#		  '===',
#		  sep = '\n',
#		  file = stderr)

#def debug_supervisor(message): # Takes a message

#	print(*message, file = stderr)

#def debug_task(task): # Takes a process object
	
#	print(str(task.path),
#		  task.op,
#		  sep = '\t',
#		  file = stderr)

def error( # Prints error information
	name: str,
	line: int,
	status: str,
	args: tuple[str, ...]
	) -> None:

	print('===',
	      '{0} (line {1})'.format(name, line),
		  ERRORS[status].format(*args) if args else ERRORS[status],
		  '===',
		  sep = '\n',
		  file = stderr)