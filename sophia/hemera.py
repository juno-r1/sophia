def debug_tree(node, level = 0): # Takes a parse tree
	
	print(repr(getattr(node, 'n', 0)).zfill(4) + '\t' + ('  ' * level) + repr(node)) # n is the unique id of a node, if enabled
	if node.nodes: # True for non-terminals, false for terminals
		level += 1 # This actually works, because parameters are just local variables, for some reason
		for item in node.nodes:
			debug_tree(item, level)

def debug_process(process): # Takes a process object

	print(repr(process))

def debug_memory(memory): # Takes the namespace hierarchy
	
	for namespace in tuple(memory.values())[1:]: # Excludes namespace lock
		print(repr(namespace))

def debug_namespace(process): # Takes a process object
	
	print(repr(process.namespace[process.pid]))