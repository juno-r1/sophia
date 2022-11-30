# ☉
# 08/05/2022: Parser implemented (first working version)
# 15/07/2022: Hello world program
# 04/08/2022: Fibonacci program
# 09/08/2022: Basic feature set implemented (0.0)
# 16/08/2022: Basic feature set re-implemented (0.1)
# 20/08/2022: Type system implemented (0.1)

import arche, hemera, kadmos, kleio

class runtime: # Base runtime object

	def __init__(self, start): # God objects? What is she objecting to?

		self.modules = [module(start)] # Initialises start module
		self.builtins = tuple(kleio.definition(*item) for item in arche.init_types() + arche.init_functions() + arche.init_operators()) # Initialises built-ins
		self.routines = [kleio.coroutine(self.modules[0].name, self, None)] # Creates runtime binding
		self.node = self.modules[0] # Current node; sets initial module as entry point
		self.value = None # Current value
		self.address = None # Address register

	def execute(self): # Runs the module
		
		while self.node: # Runtime loop
			hemera.debug_runtime(self)
			path = self.routines[-1].path[-1]
			if isinstance(self.value, kleio.control): # Handles control flow: continue, break, return, yield
				if self.value.name == 'cast':
					self.node, self.address = self.address, None
					yield self.value.value
				elif self.value.name in ('return', 'send'):
					self.value = self.routines[-1].instances[0].send(self.value) # Guaranteed to send to the coroutine instance
				else:
					while not isinstance(self.node, (while_statement, for_statement)): # Traverses up to closest enclosing loop - bootstrap assumes that interpreter is well-written and one exists
						self.node = self.node.head
						self.routines[-1].instances.pop()
						self.routines[-1].path.pop()
					if self.value.name == 'continue':
						self.value = self.routines[-1].instances[-1].send(self.value)
					elif self.value.name == 'break':
						main.branch()
					self.value = None
			elif self.address: # If destination specified by node:
				if isinstance(self.node, coroutine) and (path < 0 or path >= len(self.node.nodes)):
					self.routines.pop()
				self.node, self.address = self.address, None # Move to addressed node
				self.value = self.routines[-1].instances[-1].send(self.value)
			elif self.node.nodes and 0 <= path < len(self.node.nodes): # Walk down
				self.node.nodes[path].head = self.node # Sets child head to self
				self.node = self.node.nodes[path] # Set value to child node
				self.routines[-1].path.append(0)
				if isinstance(self.node, coroutine):
					self.branch() # Adds new counter to stack, skipping all nodes
				self.routines[-1].instances.append(self.node.execute()) # Initialises generator
				self.value = self.routines[-1].instances[-1].send(None) # Somehow, it's never necessary to yield a value down the tree
			else: # Walk up
				while (path < 0 or path >= len(self.node.nodes)) and not self.address: # While last node of branch:
					path = self.routines[-1].path[-2]
					self.routines[-1].instances.pop() # Removes generator
					self.node = self.node.head # Walk upward
					path = path + 1
					if self.routines[-1].path.pop() != -1: # Skip else statements if not branch
						while path < len(self.node.nodes) and isinstance(self.node.nodes[path], else_statement):
							path = path + 1
					self.branch(path) # Increment path counter
					if isinstance(self.node, module): # Check if finished
						if path == len(self.node.nodes):
							self.node = None
						break # Can't send to self
					self.value = self.routines[-1].instances[-1].send(self.value)
					if isinstance(self.value, kleio.control):
						break
					path = self.routines[-1].path[-1]
					hemera.debug_runtime(self)
		else:
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
		
		for item in self.builtins: # Searches built-ins first; built-ins are independent of namespaces
			if item.name == name: # If the name is a built-in:
				return item # Return the binding
		for routine in self.routines[::-1]: # Searches module in reverse order
			for item in routine.namespace:
				if item.name == name: # If the name is bound in the runtime:
					return item # Return the binding
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
		self.routines[-1].namespace.extend((kleio.definition(param.value, main.cast(args[i], param.type), param.type, True) for i, param in enumerate(params))) # Bind parameters to namespace

	def cast(self, value, type_value): # Checks type of value and returns boolean
				
		binding = self.find(type_value).value
		type_node = getattr(binding, 'entry', binding)
		stack = []
		while isinstance(type_node, type_statement): # Get all supertypes for type
			stack.append(type_node)
			type_node = self.find(type_node.supertype).value
		else:
			stack.append(type_node) # Guaranteed to be a built_in
		while stack: # Check type down the entire tree
			type_node = stack.pop()
			if isinstance(type_node, type_statement): # If user-defined:
				type_node.exit = main.value # Store source address in destination node
				address, main.address = main.address, type_node # Set address to function node
				main.call(type_node) # Creates a coroutine binding in main
				self.routines[-1].namespace[0].value, self.routines[-1].namespace[0].type = value, type_value # Manually bind cast value to type binding
				return_value = main.execute().send(None) # Creates new instance of runtime loop: oh god, oh fuck, et cetera
				main.address = address # Restores address if one was set when cast() was called
			else: # If built-in:
				return_value = type_node(value) # Corrects type for built-ins
			if return_value is None:
				raise TypeError('Failed cast to ' + type_value + ': ' + repr(value))
		else:
			return return_value # Return indicates success; cast() raises an exception on failure

class node: # Base node object

	n = 0 # Accumulator for unique index; used for debug info

	def __init__(self, value, *nodes): # Do not store state in nodes

		self.n, node.n = node.n, node.n + 1
		self.value = value # For operands that shouldn't be evaluated or that should be handled differently
		self.scope = 0
		self.head = None
		self.nodes = [i for i in nodes] # For operands that should be evaluated

	def routine(self): # Gets node's routine

		routine = self
		while not isinstance(routine, coroutine):
			routine = routine.head
		else:
			return routine

	def parse(self, data): # Recursively descends into madness and creates a tree of nodes with self as head

		lines, tokens, scopes = [kadmos.line_split(line) for line in data.splitlines() if line], [], [] # Splits lines into symbols and filters empty lines

		for line in lines: # Tokenises each item in lines
			scope = line.count('\t') # Gets scope level from number of tabs
			if not line[scope:]:
				continue # Skips empty lines
			if not kadmos.balanced(line):
				raise SyntaxError('Unmatched parentheses')
			tokens.append([])
			scopes.append(scope)
			for n, symbol in enumerate(line[scope:]): # Skips tabs
				if (symbol[0] in kadmos.characters or symbol[0] in ("'", '"')) and (symbol not in ('not', 'or', 'and', 'xor')): # Quick test for literal
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
						if symbol in ('^', ',', ':'):
							token = infix_r(symbol)
						elif symbol == '<-':
							token = bind(symbol)
						elif symbol == '->':
							token = send(symbol)
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
			else: # Tokenises expressions
				token = lexer(line).parse() # Passes control to a lexer object that returns an expression tree when parse() is called
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

class module(coroutine): # Module object is always the top level of a syntax tree

	def __init__(self, file_name):

		super().__init__(self) # Sets initial node to self
		with open(file_name, 'r') as f: # Binds file data to runtime object
			self.file_data = f.read() # node.parse() takes a string containing newlines
		self.parse(self.file_data) # Here's tree
		self.name = file_name.split('.')[0]

	def execute(self):
		
		while main.routines[-1].path[-1] <= len(self.nodes): # Allows more fine-grained control flow than using a for loop
			yield
		else:
			main.address = main.routines.pop().exit

class type_statement(coroutine):

	def __init__(self, tokens):
		
		super().__init__([tokens[1]]) # Type
		if len(tokens) > 3: # Naive check for subtyping
			self.supertype = tokens[3].value
			if self.supertype in kadmos.sub_types: # Corrects shortened type names
				self.supertype = kadmos.sub_types[self.supertype]
		else:
			self.supertype = 'untyped'

	def execute(self):

		ops = (kleio.definition(item.value[0].value, item, item.value[0].type, reserved = True) for item in self.nodes if isinstance(item, function_definition)) # Initialises type operations
		routine = kleio.coroutine(self.value[0].value, self, None, *ops) # Creates type binding with type operations
		main.bind(self.value[0].value, routine, self.value[0].value, reserved = True) # Binds coroutine information with type operations to namespace
		return_value = None
		while True: # Execution loop
			return_value = yield return_value
			while main.routines[-1].path[-1] < len(self.nodes): # Allows more fine-grained control flow than using a for loop
				status = yield
				if isinstance(status, kleio.control): # Failed constraints pass back here
					return_value = None
					main.address = main.routines.pop().exit
					break
			else: # Default behaviour for no return or yield
				return_value = main.find(self.value[0].value).value
				main.address = main.routines.pop().exit
			return_value = kleio.control('cast', return_value)

class function_definition(coroutine):

	def __init__(self, tokens):

		super().__init__(tokens[0:-1:2]) # Sets name and a list of parameters as self.value

	def execute(self):
		
		main.bind(self.value[0].value, self, self.value[0].type, reserved = True)
		return_value = None
		while True: # Execution loop
			yield return_value
			while main.routines[-1].path[-1] <= len(self.nodes): # Allows more fine-grained control flow than using a for loop
				status = yield return_value
				if isinstance(status, kleio.control): # Return and yield statements pass back here
					return_value = status.value # Check for output type in function call, not in function
					if status.name == 'return':
						main.address = main.routines.pop().exit
						break
					if status.name == 'send':
						return_value = main.routines.pop() # Returns the active coroutine frame
						return_value.value = status.value # Stores display value
						if isinstance(main.find(return_value.name).value, kleio.coroutine): # Checks if coroutine is bound
							main.bind(return_value.name, return_value) # Updates namespace binding
						if status.address: # Handles address
							if status.address == main.routines[-1].name:
								raise ValueError('Attempted send to active routine')
							routine = main.find(status.address).value # This basically needs to behave like a function call except for a bound coroutine
							if not isinstance(routine, kleio.coroutine):
								raise TypeError('Invalid send address')
							routine.exit = return_value.exit # Transfers over routine exit
							main.address = routine.entry
							main.routines.append(routine)
						else:
							main.address = return_value.exit
			else: # Default behaviour for no return or yield
				return_value = main.cast(None, self.value[0].type)
				main.address = main.routines.pop().exit

class assignment(node):

	def __init__(self, tokens):

		super().__init__(tokens[0], lexer(tokens[2:]).parse())

	def execute(self):
		
		value = yield # Yields to main
		yield main.bind(self.value.value, main.cast(value, self.value.type), self.value.type) # Yields to go up

class if_statement(node):

	def __init__(self, tokens):

		super().__init__(None, lexer(tokens[1:-1]).parse())

	def execute(self):

		condition = yield
		if condition is True:
			while main.routines[-1].path[-1] <= len(self.nodes):
				yield
		elif condition is False:
			yield main.branch()
		else: # Over-specify on purpose to implement Sophia's specific requirement for a boolean
			raise ValueError('Condition must evaluate to boolean')

class while_statement(node):

	def __init__(self, tokens):

		super().__init__(None, lexer(tokens[1:-1]).parse())

	def execute(self):

		condition = yield
		if condition is not True and condition is not False: # Over-specify on purpose to implement Sophia's specific requirement for a boolean
			raise ValueError('Condition must evaluate to boolean')
		elif condition is False:
			yield main.branch()
		while condition:
			while main.routines[-1].path[-1] < len(self.nodes):
				status = yield
				if isinstance(status, kleio.control):
					break
			main.branch(0) # Repeat nodes
			condition = yield
		else:
			yield main.branch(len(self.nodes)) # Skip nodes

class for_statement(node):

	def __init__(self, tokens):

		super().__init__(tokens[1], lexer(tokens[3:-1]).parse())

	def execute(self):

		index = self.value
		sequence = yield
		sequence = iter(sequence)
		main.bind(index.value, None, index.type)
		try:
			while True: # Loop until the iterator is exhausted
				main.bind(index.value, next(sequence), index.type) # Binds the next value of the sequence to the loop index
				while main.routines[-1].path[-1] < len(self.nodes):
					status = yield
					if isinstance(status, kleio.control):
						break
				main.branch(1) # Repeat nodes
		except StopIteration: # Break
			main.unbind(index.value) # Unbinds the index
			yield main.branch(len(self.nodes)) # Skip nodes

class else_statement(node):

	def __init__(self, tokens):

		super().__init__(None)
		if len(tokens) > 2: # Non-final else
			head = globals()[tokens[1].value + '_statement'](tokens[1:]) # Tokenise head statement
			self.value, self.nodes, self.execute = head.value, head.nodes, head.execute # Else statement pretends to be its head statement
			del head # So no head?

	def execute(self): # Final else statement; gets overridden for non-final
		
		while main.routines[-1].path[-1] <= len(self.nodes):
			yield

class assert_statement(node):

	def __init__(self, tokens):

		nodes, sequence = [], []
		for token in tokens[1:-1]: # Collects all expressions in head statement
			if token.value == ',':
				nodes.append(lexer(sequence).parse())
				sequence = []
			else:
				sequence.append(token)
		else:
			nodes.append(lexer(sequence).parse())
			super().__init__(None, *nodes)
			self.length = len(nodes)

	def execute(self):
		
		while main.routines[-1].path[-1] < self.length: # Evaluates all head statement nodes
			value = yield
			if value is None: # Catches null expressions
				yield main.branch()
		while main.routines[-1].path[-1] <= len(self.nodes):
			yield
	
class constraint_statement(node):

	def __init__(self, tokens):

		super().__init__(None)

	def execute(self):

		while main.routines[-1].path[-1] < len(self.nodes):
			constraint = yield
			if constraint is not True and constraint is not False:
				raise ValueError('Constraint must evaluate to boolean')
			if constraint is False:
				yield kleio.control('return', None) # Functionally identical
		yield

class return_statement(node):

	def __init__(self, tokens):
		
		if len(tokens) > 1:
			super().__init__(None, lexer(tokens[1:]).parse())
		else:
			super().__init__(None)

	def execute(self):
		
		if self.nodes:
			value = yield # If tail call, control never returns back here 
		else:
			value = None
		yield kleio.control('return', value) # Sends return control with return value

class yield_statement(node):

	def __init__(self, tokens):

		if len(tokens) > 1:
			super().__init__(None, lexer(tokens[1:]).parse())
		else:
			super().__init__(None)

	def execute(self):
			
		if self.nodes:
			value = yield
		else:
			value = None
		main.routines[-1].entry = self
		value = yield kleio.control('send', value) # Sends send control with send value and no address and awaits value
		yield value

class link_statement(node):

	def __init__(self, tokens):

		super().__init__(None, *tokens[1::2]) # Allows multiple links

	def execute(self):

		pass # I don't know how to implement this yet

class import_statement(node):

	def __init__(self, tokens):

		super().__init__(None, *tokens[1::2]) # Allows multiple imports

	def execute(self):

		for item in self.nodes:
			main.module = runtime(item.value + '.sophia')
			main.module.run(do_import = True)
			main.bind(item.value, main.module, 'module')
			main.module = None

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
		
		if self.value[0] in '.0123456789': # Terrible way to check for a number without using a try/except block
			value = float(self.value) # Attempt to cast to float
			if value % 1 == 0:
				value = int(value) # Attempt to cast to int
		elif self.value[0] in ('"', "'"):
			value = self.value[1:-1] # Interpret as string
		elif self.value in kadmos.sub_values:
			value = kadmos.sub_values[self.value] # Interpret booleans and null
		else: # If reference:
			try:
				value = main.find(self.value).value
				if isinstance(value, kleio.coroutine) and not isinstance(self.head, bind):
					value = value.value # Evaluates to display value unless bound or invoked in a send
				value = main.cast(value, self.type) # Returns value referenced by name
			except (NameError, TypeError) as status:
				if isinstance(self.head, assert_statement) and main.routines[-1].path[-1] < self.head.length: # Allows assert statements to reference unbound names without error
					value = None
				else:
					raise status

		yield value # Send value to main

class keyword(identifier): # Adds keyword behaviours to a node

	def nud(self, lex):

		return self

	def execute(self):

		if self.value is None: # Represents zero-argument function call
			yield ()
		else:
			yield kleio.control(self.value) # Control object handling continue and break

class operator(node): # Generic operator node

	def __init__(self, value):

		super().__init__(value)
		self.lbp = kadmos.find_bp(value) # Gets binding power of symbol

class prefix(operator): # Adds prefix behaviours to a node

	def nud(self, lex):

		self.nodes = [lex.parse(self.lbp)]
		return self

	def execute(self): # Unary operators

		op = main.find(self.value) # Gets the operator definition
		x = yield
		yield op.value[0](x) # Implements unary operator

class infix(operator): # Adds infix behaviours to a node

	def led(self, lex, left):
		
		self.nodes = [left, lex.parse(self.lbp)]
		return self

	def execute(self):
		
		op = main.find(self.value) # Gets the operator definition
		x = yield
		y = yield
		yield op.value[1](x, y) # Implements left-binding binary operator

class infix_r(operator): # Adds right-binding infix behaviours to a node

	def led(self, lex, left):
		
		self.nodes = [left, lex.parse(self.lbp - 1)]
		return self

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
			yield op.value[1](x, y) # Implements right-binding binary operator

class bind(operator): # Defines the bind operator

	def led(self, lex, left): # Parses like a binary operator but stores the left operand like assignment
		
		self.value, self.nodes = left, [lex.parse(self.lbp)]
		return self

	def execute(self):

		value = yield
		if isinstance(value, kleio.coroutine):
			value.name = self.value.value # Stores binding name in coroutine
			data = value.value
		else:
			data = value
		try:
			data = main.cast(data, self.value.type) # Checks data type of bind
		except TypeError as status:
			if isinstance(self.head, assert_statement) and main.routines[-1].path[-1] <= self.head.length:
				yield
			else:
				raise status
		print(self.value.value)
		main.bind(self.value.value, value, self.value.type)
		yield data

class send(operator): # Defines the send operator

	def led(self, lex, left): # Parses like a binary operator but stores the right operand like assignment
		
		self.nodes, self.value = [left], lex.parse(self.lbp)
		return self

	def execute(self):

		arg = yield # Sending only ever takes 1 argument
		main.routines[-1].entry = self
		value = yield kleio.control('send', arg, self.value.value) # Send argument to entry point of routine
		if isinstance(value, kleio.coroutine):
			data = value.value
		else:
			data = value
		try:
			data = main.cast(data, self.value.type) # Checks data type of routine output
		except TypeError as status:
			if isinstance(self.head, assert_statement) and main.routines[-1].path[-1] <= self.head.length:
				yield
			else:
				raise status
		yield data

class left_bracket(operator): # Adds left-bracket behaviours to a node

	def nud(self, lex): # For normal parentheses
		
		self.nodes = [lex.parse(self.lbp)]
		lex.use()
		return self # The bracketed sub-expression as a whole is essentially a literal

	def led(self, lex, left): # For function calls
		
		self.nodes = [left, lex.parse(self.lbp)]
		lex.use()
		return self # The bracketed sub-expression as a whole is essentially a literal

class function_call(left_bracket):

	def execute(self):

		routine = yield
		args = yield
		if not isinstance(args, tuple): # Type correction
			args = tuple([args]) # Very tiresome type correction, at that
		if isinstance(routine, function_definition): # If user-defined:
			if isinstance(self.head, return_statement): # Tail call
				routine.exit = main.routines[-1].exit # Exits directly out of scope
				routine.tail = True
			else:
				routine.exit = self # Store source address in destination node
				routine.tail = False
			main.address = routine # Set address to function node
			main.call(routine, *args) # Creates a coroutine binding in main
			value = yield # Function yields back into call to store return value
			try:
				if isinstance(value, kleio.coroutine):
					if isinstance(self.head, bind):
						data = value
						data.value = main.cast(data.value, routine.value[0].type) # Checks data type of routine output
					else:
						data = value.value
						data = main.cast(data, routine.value[0].type) # Checks data type of routine output
				else:
					data = value
					data = main.cast(data, routine.value[0].type) # Checks data type of routine output
			except TypeError as status:
				if isinstance(self.head, assert_statement) and main.routines[-1].path[-1] <= self.head.length:
					yield
				elif self.head.head and isinstance(self.head, bind) and isinstance(self.head.head, assert_statement) and main.routines[-1].path[-2] <= self.head.head.length:
					yield
				else:
					raise status
			yield data
		else: # If built-in:
			if hasattr(routine, '__call__'): # No great way to check if a Python function is, in fact, a function
				if args: # Python doesn't like unpacking empty tuples
					yield routine(*args) # Since routine is a Python function in this case
				else:
					yield routine()
			else:
				raise TypeError(routine.__name__ + ' is not a function')

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
		
		if len(self.nodes) > 1:
			raise SyntaxError('Meta-statement forms invalid expression')
		data = yield # Evaluate string
		self.parse(data) # Run-time parser stage
		value = yield # Yield into evaluated statement or expression
		self.nodes = [self.nodes[0]]
		yield value # Yield value, if it has one

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

class lexer: # Lex object to get around not being able to peek the next value of an iterator

	def __init__(self, tokens):

		self.lexes = (iter(tokens), iter(tokens))
		self.token = None
		self.peek = next(self.lexes[1])

	def use(self): # Gets the next tokens

		self.token = next(self.lexes[0])
		try:
			self.peek = next(self.lexes[1])
		except StopIteration:
			self.peek = eol()

	def parse(self, lbp = 0): # Pratt parser for expressions - takes a lex construct and the left-binding power

		self.use()
		if isinstance(self.peek, eol): # Detects end of expression
			return self.token # End-of-line token
		left = self.token.nud(self) # Executes null denotation of current token
		while lbp < self.peek.lbp:
			self.use()
			left = self.token.led(self, left) # Executes left denotation of current token
			if isinstance(self.peek, eol): # Detects end of expression
				return left # Returns expression tree
		else:
			return left # Preserves state of next_token for higher-level calls

	# https://eli.thegreenplace.net/2010/01/02/top-down-operator-precedence-parsing
	# https://abarker.github.io/typped/pratt_parsing_intro.html
	# https://web.archive.org/web/20150228044653/http://effbot.org/zone/simple-top-down-parsing.htm
	# https://matklad.github.io/2020/04/13/simple-but-powerful-pratt-parsing.html

main = runtime('test.sophia') # Initialises runtime object
main.routines[-1].instances.append(main.modules[0].execute()) # Starts runtime loop at initial module
main.routines[-1].instances[-1].send(None)
main.execute().send(None) # Executes runtime object