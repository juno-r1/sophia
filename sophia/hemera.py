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

def debug_process(runtime): # Takes a runtime object

	name = type(runtime.node).__name__
	value = runtime.node.value
	if name == 'module':
		value = runtime.node.name
	elif isinstance(value, list):
		value = [item.type + ' ' + item.value for item in value]
	elif type(value).__name__ == 'literal':
		value = value.value
	print(repr(getattr(runtime.node, 'n', 0)).zfill(4), name, value, runtime.routines[-1].path[-1])

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