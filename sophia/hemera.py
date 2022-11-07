def debug_tree(tree, level = 0): # Takes a parse tree

	n = repr(getattr(tree, 'n', 0)).zfill(4) # Unique id of node, if enabled
	if tree.nodes: # True for non-terminals, false for terminals
		level += 1 # This actually works, because parameters are just local variables, for some reason
		if tree.value:
			if isinstance(tree.value, str):
				print(n, '\t', ('  ' * level), tree.value)
			elif isinstance(tree.value, list):
				print(n, '\t', ('  ' * level), [x.value for x in tree.value])
			else:
				print(n, '\t', ('  ' * level), tree.value.value)
		else:
			print(n, '\t', ('  ' * level), type(tree).__name__)
		for item in tree.nodes:
			debug_tree(item, level)
	else:
		level += 1
		print(n, '\t', ('  ' * level), tree.value)

def debug_runtime(runtime): # Takes a runtime object

	name = type(runtime.value).__name__
	value = runtime.value.value
	if name == 'runtime':
		value = runtime.name
	elif isinstance(value, list):
		value = [item.type + ' ' + item.value for item in value]
	elif type(value).__name__ == 'literal':
		value = value.value
	print(repr(getattr(runtime.value, 'n', 0)).zfill(4), name, value, runtime.routines[-1].path[-1])

def debug_memory(runtime): # Takes a runtime object

	print('===')
	for routine in runtime.routines:
		debug_module(routine)
		print('===')

def debug_module(routine): # Takes a routine object

	for i, binding in enumerate(routine.namespace):
		name = type(binding.value).__name__
		if name == 'runtime':
			print(binding.name, 'module', [item.name for item in binding.value.namespace[0]])
		elif name == 'type_statement' and hasattr(binding.value, 'namespace'):
			print(binding.name, 'type', [item.name for item in binding.value.namespace])
		else:
			print(binding.name, binding.type, repr(binding.value))
		if i != len(routine.namespace) - 1:
			print('---')