# ☉
# 08/05/2022: Parser implemented (first working version)
# 15/07/2022: Hello world program
# 04/08/2022: Fibonacci program
# 09/08/2022: Basic feature set implemented (0.0)
# 16/08/2022: Basic feature set re-implemented (0.1)
# 20/08/2022: Type system implemented (0.1)

import arche, hemera, kadmos, kleio

class node: # Base node object

	n = 0 # Accumulator for unique index; used for debug info

	def __init__(self, value, *nodes): # Do not store state in nodes

		self.n, node.n = node.n, node.n + 1
		self.value = value
		self.scope = 0
		self.head = None
		self.nodes = [i for i in nodes]

	def routine(self): # Gets node's routine

		routine = self
		while not isinstance(routine, coroutine):
			routine = routine.head
		else:
			return routine

	def parse(self, data): # Recursively descends into madness and creates a tree of nodes with self as head

		lines, tokens, scopes = [kadmos.line_split(line) for line in data if line], [], [] # Splits lines into symbols and filters empty lines

		for line in lines: # Tokenises each item in lines
			scope = line.count('\t') # Gets scope level from number of tabs
			if not line[scope:]:
				continue # Skips empty lines
			if not kadmos.balanced(line):
				raise SyntaxError('Unmatched parentheses')
			tokens.append([])
			scopes.append(scope)
			for n, symbol in enumerate(line[scope:]): # Skips tabs
				if (symbol[0] in kadmos.characters or symbol[0] in ["'", '"']) and (symbol not in ['not', 'or', 'and', 'xor']): # Quick test for literal
					if symbol in kadmos.structure_tokens or symbol in kadmos.keyword_tokens:
						token = keyword(symbol)
					else:
						token = literal(symbol)
						if len(tokens[-1]) > 0 and isinstance(tokens[-1][-1], literal): # Checks for type
							token_type = tokens[-1].pop().value # Gets type of identifier 
							if token_type in kadmos.sub_types: # Corrects shortened type names
								token_type = kadmos.sub_types[token_type]
							token.type = token_type # Sets type of identifier
				else:
					if symbol in kadmos.parens[0::2]:
						if symbol == '(':
							if isinstance(tokens[-1][-1], literal):
								token = function_call(symbol)
							else:
								token = parenthesis(symbol)
						elif symbol == '[':
							if isinstance(tokens[-1][-1], literal):
								token = sequence_index(symbol)
							else:
								token = sequence_literal(symbol)
						elif symbol == '{':
							token = meta_statement(symbol)
					elif symbol in kadmos.parens[1::2]:
						if isinstance(tokens[-1][-1], left_bracket):
							tokens[-1].append(keyword(None)) # Zero-argument function call
						token = right_bracket(symbol)
					elif tokens[-1] and isinstance(tokens[-1][-1], (literal, right_bracket)): # If the preceding token is a literal (if the current token is an infix):
						if symbol in ['^', '.', ',', ':']:
							token = infix_r(symbol)
						else:
							token = infix(symbol)
					else:
						token = prefix(symbol) # NEGATION TAKES PRECEDENCE OVER EXPONENTIATION - All unary operators have the highest possible left-binding power
				tokens[-1].append(token)
				
		parsed = []

		for line in tokens: # Tokenises whole lines
			if line[0].value in kadmos.structure_tokens:
				token = globals()[line[0].value + '_statement'](line) # Cheeky little hack that makes a node for whatever structure keyword is specified
			elif line[0].value in kadmos.keyword_tokens:
				token = line[0] # Keywords will get special handling later
			elif line[-1].value == ':':
				token = function_definition(line)
			elif len(line) > 1 and line[1].value == ':':
				token = assignment(line)
			elif len(line) > 1 and line[1].value == 'is':
				token = alias(line)
			else: # Only necessary because of function calls with side effects
				token = expression(line)
			parsed.append(token)

		head, last = self, self # Head token and last line

		for i, line in enumerate(parsed): # Groups lines based on scope
			line.scope = scopes[i] + 1 # Add 1 since main has scope 0
			if line.scope > head.scope + 1: # If entering scope
				head = last # Last line becomes the head node
			elif line.scope < head.scope + 1: # If exiting scope
				if line.scope > 1: # If statement is in local scope:
					for n in parsed[i::-1]: # Find the last line containing the current line in its direct scope, searching backwards from the current line
						if n.scope == line.scope - 1: # If such a line is found:
							head = n # Make it the head node
							break
				else: # If statement is in global scope:
					head = self # Resets head to main node
			head.nodes.append(line) # Link nodes
			last = line
		else:
			hemera.debug_tree(self) # Uncomment for parse tree debug information
			print('===')
			return self

class coroutine(node): # Base coroutine object

	def __init__(self, value, *tokens):

		super().__init__(value, *tokens)
		self.exit = None # Tracks most recent caller of coroutine
		self.tail = False # Tracks call type

class runtime(coroutine): # Runtime object contains runtime information and is the top level of the syntax tree

	def __init__(self, file_name): # God objects? What is she objecting to?

		super().__init__(self) # Sets initial node to self
		with open(file_name, 'r') as f: # Binds file data to runtime object
			self.file_data = f.read().splitlines()
		self.parse(self.file_data) # Here's tree
		self.name = file_name.split('.')[0]
		self.address = None
		self.builtins = [kleio.definition(*item) for item in arche.init_types() + arche.init_functions() + arche.init_operators()] # Initialises built-ins
		self.routines = [kleio.coroutine(self.name, self, None, *self.builtins)] # Creates runtime binding

	def execute(self): # Runs the module
		
		value = None # Value register
		while self.value: # Execution loop
			path = self.routines[-1].path[-1]
			#hemera.debug_runtime(self)
			if self.address: # If destination specified by node:
				#print('jump')
				if isinstance(self.value, coroutine) and (path < 0 or path >= len(self.value.nodes)):
					self.routines.pop()
				self.value, self.address = self.address, None # Move to addressed node
				if isinstance(value, Exception):
					value = self.routines[-1].instances[-1].throw(value)
				else:
					value = self.routines[-1].instances[-1].send(value)
			elif self.value.nodes and 0 <= path < len(self.value.nodes): # Walk down
				self.value.nodes[path].head = self.value # Sets child head to self
				self.value = self.value.nodes[path] # Set value to child node
				self.routines[-1].path.append(0)
				if isinstance(self.value, coroutine):
					self.branch() # Adds new counter to stack, skipping all nodes
				self.routines[-1].instances.append(self.value.execute()) # Initialises generator
				value = self.routines[-1].instances[-1].send(value)
			else: # Walk up
				while (path < 0 or path >= len(self.value.nodes)) and not self.address: # While last node of branch:
					path = self.routines[-1].path[-2]
					if not isinstance(self.value, coroutine):
						self.routines[-1].instances.pop() # Removes generator
					self.value = self.value.head # Walk upward
					path = path + 1
					if self.routines[-1].path.pop() != -1: # Skip else statements if not branch
						while path < len(self.value.nodes) and isinstance(self.value.nodes[path], else_statement):
							path = path + 1
					self.branch(path) # Increment path counter
					if self.value is self: # Check if finished
						if path == len(self.nodes):
							self.value = None
						break # Can't send to self
					value = self.routines[-1].instances[-1].send(value)
					path = self.routines[-1].path[-1]
					#hemera.debug_runtime(self)
		else:
			for item in self.routines[0].namespace[len(self.builtins) - 1::-1]: # Unbinds built-ins in reverse order to not cause problems with the loop
				self.unbind(item.name)
			hemera.debug_memory(self)
			yield self # Returns runtime object to facilitate imports

	def branch(self, path = -1):

		self.routines[-1].path[-1] = path # Skip nodes

	def bind(self, name, value, type_value = 'untyped', reserved = False): # Creates or updates a name binding in main

		for item in self.routines[-1].namespace: # Finds and updates a name binding
			if item.name == name:
				if item.reserved: # If the name is bound, or is a loop index:
					raise NameError('Binding to reserved name: ' + name)
				else:
					item.value = value
					if type_value != 'untyped':
						item.type = type_value
				break
		else: # Creates a new name binding
			self.routines[-1].namespace.append(kleio.definition(name, value, type_value, reserved))

	def unbind(self, name): # Destroys a name binding in main

		for i, item in enumerate(self.routines[-1].namespace): # Finds and destroys a name binding
			if item.name == name:
				index = i
				break
		else:
			raise NameError('Undefined name: ' + name)

		del self.routines[-1].namespace[index] # Destroy the binding outside of the loop to prevent issues with the loop

	def find(self, name): # Retrieves a name binding from a module
		
		for routine in self.routines[::-1]: # Searches module in reverse order
			for item in routine.namespace:
				if item.name == name: # If the name is in the module:
					return item # Return the binding
		else:
			raise NameError('Undefined name: ' + name)

	def call(self, routine, *args): # Creates a coroutine binding in main
		
		params = routine.value[1:] # Gets coroutine name, return type, and parameters
		if len(params) != len(args):
			raise SyntaxError('Expected {0} arguments; received {1}'.format(len(params), len(args)))
		if routine.tail:
			self.routines[-1] = kleio.coroutine(routine.value[0].value, routine, routine.exit) # Overwrite current frame
		else:
			self.routines.append(kleio.coroutine(routine.value[0].value, routine, routine.exit)) # Append new frame
		self.routines[-1].instances.append(routine.execute()) # Initialise routine instance and bind routine to namespace
		self.routines[-1].instances[-1].send(None) # Hatred
		self.routines[-1].namespace.extend([kleio.definition(param.value, main.cast(args[i], param.type), param.type, True) for i, param in enumerate(params)]) # Bind parameters to namespace

	def cast(self, value, type_value): # Checks type of value and returns boolean
				
		type_node = self.find(type_value).value
		stack = []
		while isinstance(type_node, type_statement): # Get all supertypes for type
			stack.append(type_node)
			type_node = self.find(type_node.supertype).value
		else:
			stack.append(type_node) # Guaranteed to be a built_in
		while stack: # Check type down the entire tree
			type_node = stack.pop()
			if isinstance(type_node, type_statement): # If user-defined:
				self.namespace.append([kleio.definition(type_value, value, type_value, reserved = True)]) # Bind special variable in a new scope
				for item in type_node.nodes[1:]: # Executing the node is the same as checking the value's type
					item.execute()
				else:
					return_value = value
					self.namespace.pop() # Destroy scope
			else: # If built-in:
				return_value = type_node(value) # Corrects type for built-ins
				if return_value is None:
					raise TypeError('Failed cast to ' + type_value + ': ' + repr(value))
		else:
			return return_value # Return indicates success; cast() raises an exception on failure

class type_statement(coroutine):

	def __init__(self, tokens):
		
		super().__init__(tokens[1]) # Type
		if len(tokens) > 3: # Naive check for subtyping
			self.supertype = tokens[3].value # Supertype
		else:
			self.supertype = None

	def execute(self):

		name = self.value.value
		for item in self.nodes: # Bind type operations to type node
			if isinstance(item, function_definition):
				self.namespace.append(kleio.definition(item.value[0].value, item, item.value[0].type, reserved = True))
		main.bind(name, self, 'type') # Creates an empty binding to manage scope

class function_definition(coroutine):

	def __init__(self, tokens):

		super().__init__(tokens[0:-1:2]) # Sets name and a list of parameters as self.value

	def execute(self):
		
		main.bind(self.value[0].value, self, self.value[0].type, reserved = True)
		return_value = None
		while True: # Execution loop
			yield return_value
			for item in self.nodes:
				try:
					yield
				except (arche.Return, arche.Yield) as status: # Return and yield statements pass back here
					main.address = main.routines.pop().exit
					return_value = main.cast(status.args[0], self.value[0].type)
					break
			else: # Default behaviour for no return or yield
				main.address = main.routines.pop().exit
				return_value = main.cast(None, self.value[0].type)

class assignment(node):

	def __init__(self, tokens):

		super().__init__(tokens[0], expression(tokens[2:])) # Typed assignments are always handed by typed_statement(), so this is fine

	def execute(self):
		
		value = yield # Yields to main
		main.bind(self.value.value, main.cast(value, self.value.type), self.value.type)
		yield # Yields to go up

class alias(node):

	def __init__(self, tokens):

		super().__init__([tokens[0], tokens[2]])

	def execute(self):
			
		pass

class if_statement(node):

	def __init__(self, tokens):

		super().__init__(None, expression(tokens[1:-1]))

	def execute(self):

		condition = yield
		if condition is True:
			for i in self.nodes[1:]:
				yield
		elif condition is False:
			main.branch()
		else: # Over-specify on purpose to implement Sophia's specific requirement for a boolean
			raise ValueError('Condition must evaluate to boolean')
		yield

class while_statement(node):

	def __init__(self, tokens):

		super().__init__(None, expression(tokens[1:-1]))

	def execute(self):

		condition = yield
		if condition is not True and condition is not False: # Over-specify on purpose to implement Sophia's specific requirement for a boolean
			raise ValueError('Condition must evaluate to boolean')
		try:
			while condition:
				try:
					for i in self.nodes[1:]:
						yield
					main.branch(0) # Repeat nodes
					condition = yield
				except arche.Continue: # Continue
					main.branch(0) # Repeat nodes
					continue
			else:
				yield main.branch(len(self.nodes)) # Skip nodes
		except arche.Break: # Break
			yield main.branch() # Branch

class for_statement(node):

	def __init__(self, tokens):

		super().__init__(tokens[1], expression(tokens[3:-1]))

	def execute(self):

		index = self.value
		sequence = yield
		sequence = iter(sequence)
		main.bind(index.value, None, index.type)
		try:
			while True: # Loop until the iterator is exhausted
				main.bind(index.value, next(sequence), index.type) # Binds the next value of the sequence to the loop index
				try:
					for item in self.nodes[1:]:
						yield
					main.branch(1) # Repeat nodes
				except arche.Continue: # Continue
					main.branch(1) # Repeat nodes
					continue
		except (StopIteration, arche.Break) as status: # Break
			if isinstance(status, StopIteration):
				main.branch(len(self.nodes)) # Skip nodes
			elif isinstance(status, arche.Break):
				main.branch() # Branch
			main.unbind(index.value) # Unbinds the index
			yield

class else_statement(node):

	def __init__(self, tokens):

		super().__init__(None)
		if len(tokens) > 2: # Non-final else
			head = globals()[tokens[1].value + '_statement'](tokens[1:]) # Tokenise head statement
			self.value, self.nodes, self.execute = head.value, head.nodes, head.execute # Else statement pretends to be its head statement
			del head # So no head?

	def execute(self): # Final else statement; gets overridden for non-final
		
		for item in self.nodes:
			yield
		yield # Needs extra yield to traverse back up

class assert_statement(node):

	def __init__(self, tokens):

		super().__init__(None, tokens[1])

	def execute(self):
		
		main.branch = False
		try:
			try:
				binding = main.find(self.nodes[0].value)
			except NameError: # Catches unbound names
				return None
			assert_type = self.nodes[0].type
			if assert_type == 'untyped' and binding.value is None: # Handles behaviour of untyped assertion
				return None
			else:
				main.cast(binding.value, assert_type)
		except TypeError:
			main.namespace.pop() # Cleans up from cast()
			return None
		main.bind(binding.name, binding.value, assert_type)
		for item in self.nodes[1:]:
			return_value = item.execute()
		else:
			main.branch = True
			main.bind(binding.name, binding.value, binding.type)
			return return_value
	
class constraint_statement(node):

	def __init__(self, tokens):

		super().__init__(None)

	def execute(self):

		for constraint in self.nodes:
			value = constraint.execute()
			if value is not True and value is not False:
				raise ValueError('Constraint must evaluate to boolean')
			if value is False:
				raise TypeError('Constraint failed')

class return_statement(node):

	def __init__(self, tokens):

		value = tokens[1:]
		if value:
			super().__init__(None, expression(value))
		else:
			super().__init__(None)

	def execute(self):
		
		if self.nodes:
			return_value = yield # If tail call, control never returns back here
		else:
			return_value = None
		yield main.routines[-1].instances[0].throw(arche.Return(return_value)) # Throws Return with return value

class yield_statement(node):

	def __init__(self, tokens):

		if 'to' in [token.value for token in tokens]:
			address = tokens[-1]
			value = tokens[1:-2]
		else:
			address = None
			value = tokens[1:]
		if value:
			super().__init__(address, expression(value))
		else:
			super().__init__(address)

	def execute(self):
			
		head_node = self.nodes[0].nodes[0] # Get head node
		if head_node.value == '(' and len(head_node.nodes) > 1: # If function call:
			setattr(head_node, 'tail', True)
			main.return_value = head_node # Facilitates tail call optimisation
		else:
			setattr(head_node, 'tail', False)
			main.return_value = self.nodes[0].execute()

class import_statement(node):

	def __init__(self, tokens):

		super().__init__(None, *tokens[1::2]) # Allows multiple imports

	def execute(self):

		for item in self.nodes:
			main.module = runtime(item.value + '.sophia')
			main.module.run(do_import = True)
			main.bind(item.value, main.module, 'module')
			main.module = None

class expression(node):

	def __init__(self, tokens):
		
		lex = lex_construct(tokens)
		tree, end = lex.recursive_parse(0)
		super().__init__(None, tree)

	def execute(self):

		x = yield # Yield to go down
		yield x # Yield to go up
		
	# https://eli.thegreenplace.net/2010/01/02/top-down-operator-precedence-parsing
	# https://abarker.github.io/typped/pratt_parsing_intro.html
	# https://web.archive.org/web/20150228044653/http://effbot.org/zone/simple-top-down-parsing.htm
	# https://matklad.github.io/2020/04/13/simple-but-powerful-pratt-parsing.html

class identifier(node): # Generic identifier class

	def __init__(self, value):

		super().__init__(value)
		self.lbp = 0
		self.type = 'untyped'

class literal(identifier): # Adds literal behaviours to a node

	def nud(self, lex):

		if isinstance(lex.peek, left_bracket): # If function call:
			lex.use() # Gets the next token, which is guaranteed to be a left bracket
			return lex.token.led(lex, self) # Guaranteed to call the LED of the following left bracket
		else:
			return self # Gives self as node

	def execute(self): # Terminal nodes
		
		try:
			value = float(self.value) # Attempt to cast to float
			if value % 1 == 0:
				value = int(value) # Attempt to cast to int
		except ValueError:
			if self.value[0] in ['"', "'"]:
				value = self.value[1:-1] # Interpret as string
			elif self.value == 'true':
				value = True
			elif self.value == 'false':
				value = False
			elif self.value == 'null':
				value = None
			else: # If reference:
				value = main.find(self.value).value # Returns value referenced by name
		yield value # Send value to main

class keyword(identifier): # Adds keyword behaviours to a node

	def nud(self, lex):

		return self

	def execute(self):

		if self.value is None: # Represents zero-argument function call
			yield ()
		else:
			loop = self # Traverse up to loop
			while not isinstance(loop, (while_statement, for_statement)):
				loop = loop.head
				main.routines[-1].path.pop()
				main.routines[-1].instances.pop()
			else:
				main.address = loop
				if self.value == 'continue':
					yield arche.Continue
				elif self.value == 'break':
					main.branch()
					yield arche.Break

class operator(node): # Generic operator node

	def __init__(self, value):

		super().__init__(value)
		self.lbp = kadmos.find_bp(value) # Gets binding power of symbol

class prefix(operator): # Adds prefix behaviours to a node

	def nud(self, lex):

		n, next_token = lex.recursive_parse(self.lbp)
		self.nodes = [n]
		return self, next_token

	def execute(self): # Unary operators

		op = main.find(self.value) # Gets the operator definition
		x = yield
		yield op.value[0](x) # Implements unary operator

class infix(operator): # Adds infix behaviours to a node

	def led(self, lex, left):

		n, next_token = lex.recursive_parse(self.lbp)
		self.nodes = [left, n]
		return self, next_token

	def execute(self):
		
		op = main.find(self.value) # Gets the operator definition
		x = yield
		y = yield
		yield op.value[1](x, y) # Implements binary operator

class infix_r(operator): # Adds right-binding infix behaviours to a node

	def led(self, lex, left):

		n, next_token = lex.recursive_parse(self.lbp - 1)
		self.nodes = [left, n]
		return self, next_token

	def execute(self):

		if self.value == ':': # Sorts out list slices and key-item pairs by returning them as a slice object or a dictionary
			x = yield
			y = yield
			if self.nodes and self.nodes[1].value == ':':
				value = [x] + y
			else:
				value = [x, y]
			if self.head.value == ':':
				yield value
			else:
				if isinstance(value[0], str):
					yield record_element(value)
				else:
					yield slice(value)
		elif self.value == ',': # Sorts out comma-separated parameters by returning them as a tuple
			x = yield
			y = yield
			if self.nodes and self.nodes[1].value == ',':
				value = [x] + y
			else:
				value = [x, y]
			if self.head.value == ',':
				yield value
			else:
				yield tuple(value)
		else: # Binary operators
			op = main.find(self.value) # Gets the operator definition
			x = yield
			y = yield
			yield op.value[1](x, y) # Implements binary operator

class left_bracket(operator): # Adds left-bracket behaviours to a node

	def nud(self, lex): # For normal parentheses

		n, next_token = lex.recursive_parse(self.lbp)
		self.nodes = [n]
		lex.use()
		return self, lex.peek # The bracketed sub-expression as a whole is essentially a literal

	def led(self, lex, left): # For function calls

		n, next_token = lex.recursive_parse(self.lbp)
		self.nodes = [left, n]
		lex.use()
		return self, lex.peek # The bracketed sub-expression as a whole is essentially a literal

class function_call(left_bracket):

	def execute(self):

		body = yield
		args = yield
		if not isinstance(args, tuple): # Type correction
			args = tuple([args]) # Very tiresome type correction, at that
		if isinstance(body, function_definition): # If user-defined:
			if isinstance(self.head.head, return_statement): # Tail call
				body.exit = main.routines[-1].exit # Exits directly out of scope
				body.tail = True
			else:
				body.exit = self # Store source address in destination node
				body.tail = False
			main.address = body # Set address to function node
			main.call(body, *args) # Creates a coroutine binding in main
			value = yield # Function yields back into call to store return value
			yield value
		else: # If built-in:
			if hasattr(body, '__call__'): # No great way to check if a Python function is, in fact, a function
				if args: # Python doesn't like unpacking empty tuples
					yield body(*args) # Since body is a Python function in this case
				else:
					yield body()
			else:
				raise TypeError(body.__name__ + ' is not a function')

class parenthesis(left_bracket):

	def execute(self):

		x = yield
		yield x

class sequence_index(left_bracket):

	def execute(self):
		
		value = yield
		subscript = yield
		if not isinstance(subscript, tuple):
			subscript = tuple([subscript])
		for i in subscript: # Iteratively accesses the sequence
			if isinstance(i, str):
				if i not in value:
					raise KeyError('Key not in record: ' + i)
			elif isinstance(i, slice):
				try:
					if i.nodes[1] < -1 * len(value) or i.nodes[1] > len(value): # If out of bounds:
						raise IndexError('Index out of bounds')
				except TypeError:
					raise IndexError('Value not sliceable')
			else:
				if i < -1 * len(value) or i >= len(value): # If out of bounds:
					raise IndexError('Index out of bounds')
			if isinstance(i, slice):
				if isinstance(value, str):
					value = ''.join(value) # Constructs slice of string using range
				elif isinstance(value, dict):
					value = {list(value.keys())[n]: list(value.values())[n] for n in i.value} # Constructs slice of record using range
				else:
					value = [value[n] for n in i.value] # Constructs slice of list using range
			else:
				value = value[i] # Python can handle this bit
		yield value # Return the accessed value

class sequence_literal(left_bracket):

	def execute(self):
		
		items = yield
		if isinstance(items, slice): # If slice:
			yield items.execute() # Gives slice expansion
		else:
			if not isinstance(items, tuple):
				items = [items]
			else:
				items = list(items)
		if isinstance(items[0], record_element): # If items is a key-item pair in a record
			yield {item.value[0]: item.value[1] for item in items} # Stupid way to merge a list of dictionaries
		else: # If items is a list
			if items and items != [None]: # Handles empty lists
				yield items
			else:
				yield []

class meta_statement(left_bracket):

	def execute(self):
		
		main.parse(self) # Run-time parser stage
		for item in self.nodes[1:]:
			return_value = item.execute() # Run-time execution stage
		self.nodes = [self.nodes[0]] # Erase tree
		return return_value

class right_bracket(operator): # Adds right-bracket behaviours to a node

	def __init__(self, value):

		super().__init__(value)

class eol(node): # Creates an end-of-line node

	def __init__(self):

		super().__init__(None)
		self.lbp = -1

class slice(node): # Initialised during execution

	def __init__(self, slice_list):

		if len(slice_list) == 2: # Normalises list slice
			slice_list.append(1)
		if slice_list[1] >= 0: # Correction for inclusive range
			slice_list[1] = slice_list[1] + 1
		else:
			slice_list[1] = slice_list[1] - 1
		super().__init__(range(*slice_list), *slice_list) # Stores slice and iterator

	def __iter__(self): # Overrides __iter__() method

		return iter(self.value) # Enables iteration over range without expanding slice

	def execute(self): # Returns expansion of slice

		return [i for i in self.value]

class record_element(node): # Initialised during record construction

	def __init__(self, value):

		super().__init__(value)

class lex_construct: # Lex object to get around not being able to peek the next value of an iterator

	def __init__(self, tokens):

		self.lexes = [iter(tokens), iter(tokens)]
		self.token = None
		self.peek = next(self.lexes[1])

	def use(self): # Gets the next tokens

		self.token = next(self.lexes[0])
		try:
			self.peek = next(self.lexes[1])
		except StopIteration:
			self.peek = eol()

	def recursive_parse(self, lbp): # Pratt parser for expressions - takes a lex construct and the left-binding power

		self.use()
		if isinstance(self.peek, eol): # Detects end of expression
			return self.token, self.peek # End-of-line token
		
		try: # NUD has variable number of return values
			left, next_token = self.token.nud(self) # Executes null denotation of current token
		except TypeError: # Is this a lazy substitute for an if-clause? Yes, but it works
			left, next_token = self.token.nud(self), None

		while lbp < self.peek.lbp:
			self.use()
			left, next_token = self.token.led(self, left) # Executes left denotation of current token
			if isinstance(next_token, eol): # Detects end of expression
				return left, next_token # End-of-line token

		return left, next_token # Preserves state of next_token for higher-level calls

main = runtime('test.sophia') # Initialises runtime object
main.instance = main.execute().send(None) # Initialises runtime generator