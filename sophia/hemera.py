'''
The Hemera module defines Sophia's IO interface, error messages, and debug tools.
'''

from sys import stderr

def debug_tree(node, level = 0): # Takes a parse tree
	
	print(str(node.line).zfill(4) + '\t' + ('  ' * level) + str(node), file = stderr)
	if node.nodes: # True for non-terminals, false for terminals
		level += 1 # This actually works, because parameters are just local variables, for some reason
		for item in node.nodes:
			debug_tree(item, level)
	if level == 1:
		print('===', file = stderr)

def debug_task(task): # Takes a process object

	print(str(task.node.line).zfill(4),
		  task.name,
		  task.path[-1],
		  str(task.node),
		  file = stderr)

def debug_namespace(task): # Takes a task object
	
	print('===',
	      task.name,
		  '---',
		  '\n---\n'.join((' '.join((name, task.types[name], str(value))) for name, value in task.values.items())),
		  '===',
		  sep = '\n',
		  file = stderr)

def debug_error(name, line, status, args): # Prints error information

	print('===',
	      '{0} (line {1})'.format(name, line),
		  errors[status].format(*args) if args else errors[status],
		  '===',
		  sep = '\n',
		  file = stderr)

errors = {
	'ARGS': 'Expected {0} arguments, received {1}',
	'BIND': 'Bind to reserved name: {0}',
	'CAST': 'Failed cast to {0}: {1}',
	'EVNT': 'Event has no initial',
	'FIND': 'Undefined name: {0}',
	'INDX': 'Invalid index: {0}',
	'INTR': 'Interface {0} is incompatible with type {1}',
	'TIME': 'Timeout warning' '\n' 'Press Ctrl+C to interrupt program',
	'UPRN': 'Unmatched parentheses',
	'UQTE': 'Unmatched quotes'
}