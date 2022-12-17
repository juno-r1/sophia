from multiprocessing import current_process, parent_process

def debug_tree(tree, level = 0): # Takes a parse tree

	n = repr(getattr(tree, 'n', 0)).zfill(4) # Unique id of node, if enabled
	if type(tree).__bases__[-1].__name__ in ('operator', 'identifier') and type(tree).__name__ not in ('bind', 'send'):
		line = n + '\t' + ('  ' * level)
	else:
		line = n + '\t' + ('  ' * level) + type(tree).__name__ + ' '
	if tree.nodes: # True for non-terminals, false for terminals
		level += 1 # This actually works, because parameters are just local variables, for some reason
		if tree.value:
			if isinstance(tree.value, str):
				line = line + tree.value
			elif isinstance(tree.value, list):
				line = line + repr([x.value for x in tree.value])
			else:
				line = line + repr(tree.value.value)
		print(line)
		for item in tree.nodes:
			debug_tree(item, level)
	else:
		print(line + tree.value)

def debug_process(process): # Takes a process object

	name = type(process.node).__name__
	value = process.node.value
	if name == 'module':
		value = process.node.name
	elif isinstance(value, list):
		value = [item.type + ' ' + item.value for item in value[1:]]
	elif type(value).__name__ == 'literal':
		value = value.value
	print(repr(getattr(process.node, 'n', 0)).zfill(4), current_process().name, name, value, process.path[-1], flush = True)

def debug_memory(process): # Takes a process object
	
	pass

def debug_namespace(process): # Takes a process object
	
	print(process.namespace[process.pid], flush = True)