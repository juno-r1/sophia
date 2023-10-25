'''
The Hemera module defines Sophia's IO interface, error messages, and debug tools.
'''

from sys import stderr

def stream_in(value = ''): return input(value)

def stream_out(value): print(value, sep = '')

def stream_err(value): print(value, sep = '', file = stderr)

def debug_descriptor(descriptor):

	print(descriptor.type,
		  descriptor.member,
		  descriptor.length,
		  descriptor.supertypes,
		  descriptor.supermember,
		  descriptor.specificity,
		  file = stderr)

def debug_dispatch(tree, level = 0):
	
	print(('  ' * level) + str(tree), file = stderr)
	if tree:
		debug_dispatch(tree.true, level + 1)
		debug_dispatch(tree.false, level + 1)

def debug_instructions(task):
	
	print('===', file = stderr)
	for i, instruction in enumerate(task.instructions):
		print(i,
			  instruction,
			  sep = '\t',
			  file = stderr)
	print('===', file = stderr)

def debug_namespace(task): # Takes a task object
	
	print('===',
	      task.name,
		  '---',
		  '\n---\n'.join((' '.join((name, str(task.types[name]), str(value))) for name, value in task.values.items() if name[0] not in '0123456789&')),
		  '===',
		  sep = '\n',
		  file = stderr)

def debug_supervisor(message): # Takes a message

	print(*message, file = stderr)

def debug_task(task): # Takes a process object
	
	print(str(task.path),
		  task.op,
		  sep = '\t',
		  file = stderr)

def debug_tree(node, level = 0): # Takes a parse tree
	
	print(str(node.line).zfill(4) + '\t' + ('  ' * level) + str(node), file = stderr)
	if node.nodes: # True for non-terminals, false for terminals
		level += 1 # This actually works, because parameters are just local variables, for some reason
		for item in node.nodes:
			debug_tree(item, level)
	if level == 1:
		print('===', file = stderr)

def debug_error(name, line, status, args): # Prints error information

	print('===',
	      '{0} (line {1})'.format(name, line),
		  errors[status].format(*args) if args else errors[status],
		  '===',
		  sep = '\n',
		  file = stderr)

errors = {
	'BIND': 'Bind to reserved name: {0}',
	'CAST': 'Failed cast to {0}: {1}',
	'COMP': 'Failed composition: {0} does not map onto {1}',
	'DISP': 'Failed dispatch: {0} has no signature {1}',
	'EVNT': 'Event has no initial',
	'FIND': 'Undefined name: {0}',
	'FLTR': 'Failed filter: {0} does not return boolean for {1}',
	'INDX': 'Invalid index: {0}',
	'PROT': 'Type {0} has no prototype',
	'RDCE': 'Failed reduce: empty list',
	'READ': 'Stream not readable',
	'TASK': 'Task expired',
	'TIME': 'Timeout warning' '\n' 'Enter Ctrl+C to interrupt program',
	'UPRN': 'Unmatched parentheses',
	'UQTE': 'Unmatched quotes',
	'USER': '{0}',
	'WRIT': 'Stream not writeable'
}