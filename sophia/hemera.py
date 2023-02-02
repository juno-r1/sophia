from sys import stderr

def debug_tree(node, level = 0): # Takes a parse tree
	
	print(repr(getattr(node, 'n', 0)).zfill(4) + '\t' + ('  ' * level) + repr(node), file = stderr) # n is the unique id of a node, if enabled
	if node.nodes: # True for non-terminals, false for terminals
		level += 1 # This actually works, because parameters are just local variables, for some reason
		for item in node.nodes:
			debug_tree(item, level)
	if level == 1:
		print('===', file = stderr)

def debug_task(task): # Takes a process object

	print(str(getattr(task.node, 'n', 0)).zfill(4),
		  task.pid,
		  task.path[-1],
		  repr(task.node),
		  file = stderr)

def debug_namespace(task): # Takes a task object
	
	print('===',
	      task.pid,
		  '---',
		  '\n---\n'.join((name + ' ' + str(task.types[name]) + ' ' + str(value) for name, value in task.values.items())) + '\n===',
		  sep = '\n',
		  file = stderr)

def debug_error(name, status): # Prints error information

	print('===',
	      name,
		  status,
		  '===',
		  sep = '\n',
		  file = stderr)