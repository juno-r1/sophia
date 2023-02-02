# ☉ 0.2 06-01-2023

import aletheia, arche, hemera, kadmos, kleio
import multiprocessing as mp
from fractions import Fraction as real

import cProfile

class task:

	def __init__(self, routine, args, link = False): # God objects? What is she objecting to?
		
		params = [item.value for item in routine.value[1:]] # Gets coroutine name, return type, and parameters
		types = [item.type for item in routine.value[1:]] # Get types of params
		if len(params) != len(args):
			return self.error('Expected {0} arguments, received {1}'.format(len(params), len(args)))
		self.link = link
		self.pid = id(self) # Guaranteed not to collide with other task PIDs; not the same as the PID of the pool process
		self.built_ins = aletheia.types | arche.operators | arche.functions # No type binding necessary because builtins are never bound to
		self.built_in_types = {i: 'type' for i in aletheia.types} | {i: 'operator' for i in arche.operators} | {i: 'function' for i in arche.functions}
		self.values = dict(zip(params, args)) # Dict of values for faster access
		self.types = dict(zip(params, types)) # Dict of types for correct typing
		self.reserved = [item.value for item in routine.value] # List of reserved names in the current namespace
		self.supertypes = arche.supertypes # Dict of type hierarchy
		self.node = routine # Current node; sets initial module as entry point
		self.path = [0]
		self.data = [] # Unfortunately, a stack
		self.type_data = [] # Unfortunately, another stack
		self.sentinel = None # Return value of task

	def execute(self): # Target of run()
		
		if not self.node.nodes: # Empty routine
			self.node = None
		while self.node: # Runtime loop
			#hemera.debug_task(self)
			if self.path[-1] == -1: # Branch
				self.node = self.node.head # Walk upward
				self.path.pop()
				self.path[-1] = self.path[-1] + 1
				continue # Skip start function
			elif self.path[-1] == self.node.length: # Walk up
				self.node = self.node.head # Walk upward
				if self.node:
					self.path.pop()
					self.path[-1] = self.path[-1] + 1
					while self.path[-1] < self.node.length and self.node.nodes[self.path[-1]].branch:
						self.path[-1] = self.path[-1] + 1
				else:
					continue
			else: # Walk down
				self.node = self.node.nodes[self.path[-1]] # Set value to child node
				self.path.append(0)
			if self.path[-1] == self.node.active:
				self.node.start(self)
			elif self.path[-1] == self.node.length:
				self.node.execute(self)
		else:
			hemera.debug_namespace(self)
			self.message('terminate')
			if self.link:
				return self.values
			else:
				return self.sentinel

	def get(self, type_name = 'untyped'): # Data retrieval checks for type

		value = self.data.pop()
		known = self.type_data.pop()
		if known and type_name in self.supertypes[known]: # Instantly succeeds if checked type is supertype of known type
			return value
		else:
			return self.cast(value, type_name, known)

	def send(self, value, type_name = None):
		
		self.data.append(value)
		self.type_data.append(type_name)

	def message(self, instruction = None, *args):
		
		if instruction:
			mp.current_process().stream.put([instruction, self.pid] + list(args))
		else:
			mp.current_process().stream.put(None)

	def branch(self, path = -1):

		self.path[-1] = path # Skip nodes

	def bind(self, name, value, type_name = None): # Creates or updates a name binding in main
		
		if name in self.reserved or name in self.built_ins: # Quicker and easier to do it here
			return self.error('Bind to reserved name: ' + name)
		self.values[name] = value # Mutate namespace
		if type_name:
			self.types[name] = type_name
		elif name not in self.types:
			self.types[name] = 'untyped'
		return value

	def unbind(self, name): # Destroys a name binding in the current namespace

		del self.values[name] # Delete binding if it exists in the namespace
		del self.types[name] # Internal method; should never raise KeyError

	def find(self, name): # Retrieves a binding's value in the current namespace
		
		if name in self.built_ins:
			return self.built_ins[name]
		elif name in self.values:
			return self.values[name]
		else:
			return self.error('Undefined name: ' + repr(name))

	def cast(self, value, type_name, known = None): # Checks type of value and returns boolean
		
		type_routine = self.find(type_name)
		stack = [] # Stack of user-defined types, with the requested type at the bottom
		while type_routine.supertype and type_routine.name != known: # Known type optimises by truncating stack
			stack.append(type_routine)
			type_routine = self.find(type_routine.supertype) # Type routine is guaranteed to be a built-in when loop ends, so it checks that before any of the types on the stack
		if type_routine(value) is None: # Check built-in type
			return self.error('Failed cast to ' + type_routine.__name__.split('_')[1] + ': ' + repr(value))
		while stack:
			type_routine = stack.pop()
			if type_routine(self, value) is None:
				return self.error('Failed cast to ' + type_routine.name + ': ' + repr(value))
		else:
			return value # Return indicates success; cast() raises an exception on failure

	def error(self, status): # Error handler
		
		if not isinstance(self.node, assert_statement): # Suppresses error for assert statement
			hemera.debug_error(self.pid, status)
			self.node = None # Immediately end routine

# Parse tree definitions

class node: # Base node object

	n = 0 # Accumulator for unique index; used for debug info

	def __init__(self, value, *nodes): # Do not store state in nodes
		
		self.n, node.n = node.n, node.n + 1
		self.value = value # For operands that shouldn't be evaluated or that should be handled differently
		self.type = None
		self.head = None # Determined by scope parsing
		self.nodes = [i for i in nodes] # For operands that should be evaluated
		self.length = 0 # Performance optimisation
		self.scope = 0
		self.active = -1 # Indicates path index for activation of start()
		self.branch = False

	def __repr__(self):

		return str(self.value)

	def routine(self):

		routine = self
		while not isinstance(routine, coroutine):
			routine = routine.head
		return routine

	def parse(self, data): # Recursively descends into madness and creates a tree of nodes with self as head

		lines, tokens, scopes = [kadmos.line_split(line) for line in data.splitlines() if line], [], [] # Splits lines into symbols and filters empty lines
		for line in lines: # Tokenises each item in lines
			scope = line.count('\t') # Gets scope level from number of tabs
			if not line[scope:]:
				continue # Skips empty lines
			tokens.append([])
			scopes.append(scope)
			for n, symbol in enumerate(line[scope:]): # Skips tabs
				if (symbol[0] in kadmos.characters or symbol[0] in '\'\"') and (symbol not in kadmos.keyword_operators): # Quick test for literal
					if symbol in kadmos.structure_tokens or symbol in kadmos.keyword_tokens:
						token = keyword(symbol)
						if tokens[-1] and tokens[-1][-1].value == 'else':
							tokens[-1].pop()
							token.branch = True
					else:
						if symbol[0] in '.0123456789': # Terrible way to check for a number without using a try/except block
							if '.' in symbol:
								token = literal(real(symbol)) # Cast to real by default
								token.type = 'real' # Type of literal is known at parse time
							else:
								token = literal(int(symbol)) # Cast to int
								token.type = 'integer'
						elif symbol in kadmos.sub_values:
							token = literal(kadmos.sub_values[symbol]) # Interpret booleans and null
							if isinstance(token.value, bool):
								token.type = 'boolean'
							else:
								token.type = None # Null is caught by untyped
						elif symbol[0] in '\'\"': # Strings have to be resolved at run time because they're indistinguishable from names otherwise
							token = literal(symbol[1:-1])
							token.type = 'string'
						else:
							token = name(symbol)
							if tokens[-1] and isinstance(tokens[-1][-1], name): # Checks for type
								token.type = tokens[-1].pop().value # Sets type of identifier
				else:
					if symbol in kadmos.parens[0::2]:
						if symbol == '(':
							if tokens[-1] and isinstance(tokens[-1][-1], name):
								token = function_call(symbol)
							else:
								token = parenthesis(symbol)
						elif symbol == '[':
							if tokens[-1] and isinstance(tokens[-1][-1], name):
								token = sequence_index(symbol)
							else:
								token = sequence_literal(symbol)
						elif symbol == '{':
							token = meta_statement(symbol)
					elif symbol in kadmos.parens[1::2]:
						token = right_bracket(symbol)
					elif tokens[-1] and isinstance(tokens[-1][-1], (identifier, right_bracket)): # If the preceding token is a literal (if the current token is an infix):
						if symbol in ('^', ',', ':'):
							token = infix_r(symbol)
						elif symbol == '<-':
							token = bind(symbol)
						elif symbol == '->':
							token = send(symbol)
						else:
							if len(tokens[-1]) == 1 and isinstance(tokens[-1][-1], name) and line[-1] == ':': # Special case for operator definition
								token = name(symbol)
								token.type = tokens[-1].pop().value # Sets return type of operator
							else:
								token = infix(symbol)
					else:
						if symbol == '>':
							token = receive(symbol)
						elif symbol == '*':
							token = resolve(symbol)
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
				if line[0].type == 'type' and '(' not in [token.value for token in line]:
					token = type_statement(line)
				elif line[0].value[0] in kadmos.characters: # Functions have names and operators have symbols
					token = function_statement(line)
				else:
					token = operator_statement(line)
			elif len(line) > 1 and line[1].value == ':':
				token = assignment(line)
			else: # Tokenises expressions
				token = kadmos.lexer(line).parse() # Passes control to a lexer object that returns an expression tree when parse() is called
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

		node, node.length, path = self, len(self.nodes), [0]
		while node: # Pre-runtime loop completes node linking and sets length
			if path[-1] == node.length: # Walk up
				node = node.head # Walk upward
				if node:
					path.pop()
					path[-1] = path[-1] + 1
			else: # Walk down
				node.nodes[path[-1]].head = node # Set head
				node = node.nodes[path[-1]] # Set value to child node
				node.length = len(node.nodes) # Set length
				path.append(0)
		else:
			#hemera.debug_tree(self) # Uncomment for parse tree debug information
			return self

class coroutine(node): # Base coroutine object

	def __init__(self, value):

		super().__init__(value)
		self.active = 0

	def __repr__(self):
		
		return str([str(item.type) + ' ' + str(item.value) for item in self.value])

class module(coroutine): # Module object is always the top level of a syntax tree

	def __init__(self, file_name):

		super().__init__(value = [self]) # Sets initial node to self
		with open(file_name, 'r') as f: # Binds file data to runtime object
			self.file_data = f.read() # node.parse() takes a string containing newlines
		self.name, self.type = file_name.split('.')[0], 'untyped'
		self.active = -1
		self.parse(self.file_data) # Here's tree

	def __repr__(self):

		return 'module ' + self.name

	def execute(self, routine):
		
		routine.node = None

class type_statement(coroutine):

	def __init__(self, tokens):
		
		super().__init__([tokens[0]]) # Type and type parameter
		self.name, self.type = tokens[0].value, tokens[0].value
		if len(tokens) > 2: # Naive check for subtyping
			self.supertype = tokens[2].value
		else:
			self.supertype = 'untyped'
		param = name(tokens[0].value)
		param.type = self.supertype
		self.value.append(param)
		self.namespace = [] # Persistent namespace of type operations

	def __call__(self, routine, value): # Initialises type routine
		
		routine.message('call', self, [value])
		return routine.calls.recv()

	def start(self, routine): # Initialises type
		
		routine.bind(self.name, self, 'type')
		routine.supertypes[self.name] = [self.name] + routine.supertypes[self.supertype]
		for node in self.nodes:
			if aletheia.sophia_function(node) and node.value[1].value == self.name: # Detect type operation
				self.namespace.append(node)
		routine.branch() # Skips body of routine

	def execute(self, routine):
		
		routine.sentinel = routine.find(self.name) # Returns cast value upon success
		routine.node = None

class operator_statement(coroutine):

	def __init__(self, tokens):

		super().__init__([token for token in tokens[0:-1:2] if token.value != ')']) # Sets operator symbol and a list of parameters as self.value
		self.name, self.type = tokens[0].value, tokens[0].type
		self.types = [item.type for item in self.value]

	def start(self, routine):
		
		routine.bind(self.name, self, 'operator')
		routine.branch() # Skips body of routine

	def execute(self, routine):
		
		routine.node = None

	def unary(self, routine, x):
		
		routine.message('call', self, [x])
		return routine.calls.recv()

	def binary(self, routine, x, y):
		
		routine.message('call', self, [x, y])
		return routine.calls.recv()

class function_statement(coroutine):

	def __init__(self, tokens):

		super().__init__([token for token in tokens[0:-1:2] if token.value != ')']) # Sets name and a list of parameters as self.value
		self.name, self.type = tokens[0].value, tokens[0].type
		self.types = [item.type for item in self.value]

	def start(self, routine):
		
		routine.bind(self.name, self, 'function')
		routine.branch() # Skips body of routine

	def execute(self, routine):
		
		routine.node = None

class assignment(node):

	def __init__(self, tokens): # Supports multiple assignment
		
		names, expressions, stack = [], [], []
		names.append(tokens.pop(0)) # Name
		tokens.pop(0) # Colon
		while tokens:
			token = tokens.pop(0)
			if token.value == ';':
				expressions.append(kadmos.lexer(stack).parse())
				names.append(tokens.pop(0))
				tokens.pop(0)
				stack = []
			else:
				stack.append(token)
		else:
			expressions.append(kadmos.lexer(stack).parse())
			super().__init__(names, *expressions)

	def __repr__(self):

		return 'assignment ' + repr([item.value for item in self.value])

	def execute(self, routine):

		values = []
		types = []
		for i in range(self.length - 1, -1, -1):
			type_name = self.value[i].type
			if not type_name:
				if self.value[i].value in routine.built_in_types:
					type_name = routine.built_in_types[self.value[i].value]
				elif self.value[i].value in routine.types:
					type_name = routine.types[self.value[i].value]
				else:
					type_name = 'untyped'
			values.append(routine.get(type_name))
			types.append(type_name)
		for i, name in enumerate(self.value):
			routine.bind(name.value, values[-1 - i], types[-1 - i])

class statement(node):

	def __repr__(self):

		if self.branch:
			return 'else ' + type(self).__name__
		else:
			return type(self).__name__

class if_statement(statement):

	def __init__(self, tokens):

		super().__init__(None, kadmos.lexer(tokens[1:-1]).parse())
		self.branch = tokens[0].branch
		self.active = 1

	def start(self, routine):

		condition = routine.get('boolean')
		if not condition:
			routine.branch()

	def execute(self, routine):
		
		return

class while_statement(statement):

	def __init__(self, tokens):

		super().__init__(None, kadmos.lexer(tokens[1:-1]).parse())
		self.branch = tokens[0].branch
		self.active = 1

	def start(self, routine):

		condition = routine.get('boolean')
		if not condition:
			routine.node = routine.node.head # Walk upward
			if routine.node:
				routine.path.pop()
				routine.path[-1] = routine.path[-1] + 1
				while routine.path[-1] < routine.node.length and routine.node.nodes[routine.path[-1]].branch:
					routine.path[-1] = routine.path[-1] + 1

	def execute(self, routine):

		routine.branch(0)

class for_statement(statement):

	def __init__(self, tokens):

		super().__init__(tokens[1], kadmos.lexer(tokens[3:-1]).parse())
		self.branch = tokens[0].branch
		self.active = 1

	def start(self, routine):
		
		sequence = arche.iterable(routine.get('iterable')) # Enables fast slice
		try:
			value = next(sequence)
			type_name = self.value.type
			if not type_name:
				if self.value.value in routine.types:
					type_name = routine.types[self.value.value]
				else:
					type_name = 'untyped'
			routine.cast(value, type_name)
			routine.bind(self.value.value, value, type_name)
			routine.send(sequence, '.index') # Stack trickery with invalid type name
		except StopIteration:
			routine.branch(self.node.length)

	def execute(self, routine):
		
		sequence = routine.data.pop() # Don't check for type
		type_name = routine.type_data.pop()
		while type_name != '.index':
			sequence = routine.data.pop()
			type_name = routine.type_data.pop()
		try:
			value = next(sequence)
			routine.cast(value, routine.types[self.value.value])
			routine.bind(self.value.value, value)
			routine.send(sequence, '.index') # .index isn't even a type
			routine.branch(1) # Skip start
		except StopIteration:
			routine.unbind(self.value.value)

class assert_statement(statement):

	def __init__(self, tokens):

		nodes, sequence = [], []
		for token in tokens[1:-1]: # Collects all expressions in head statement
			if token.value == ',':
				nodes.append(kadmos.lexer(sequence).parse())
				sequence = []
			else:
				sequence.append(token)
		else:
			nodes.append(kadmos.lexer(sequence).parse())
			super().__init__(None, *nodes)
			self.branch = tokens[0].branch
			self.active = len(nodes)

	def start(self, routine):

		for i in range(self.active):
			if routine.get(self.nodes[i].type) is None:
				return routine.branch()

	def execute(self, routine):
		
		return
	
class constraint_statement(statement):

	def __init__(self, tokens):

		super().__init__(None)
		self.branch = tokens[0].branch

	def execute(self, routine):
		
		for constraint in self.nodes:
			constraint = routine.get('boolean')
			if not constraint:
				routine.node = None
				return

class return_statement(statement):

	def __init__(self, tokens):
		
		if len(tokens) > 1:
			super().__init__(None, kadmos.lexer(tokens[1:]).parse())
		else:
			super().__init__(None)
		self.branch = tokens[0].branch

	def execute(self, routine):
		
		if self.nodes:
			routine.sentinel = routine.get(self.routine().type)
		routine.node = None

class link_statement(statement):

	def __init__(self, tokens):

		super().__init__(tokens[1::2]) # Allows multiple links
		self.branch = tokens[0].branch

	def __repr__(self):

		if self.branch:
			return 'else link_statement ' + str([repr(item) for item in self.nodes])
		else:
			return 'link_statement ' + str([repr(item) for item in self.nodes])

	#def execute(self, routine):

	#	for item in self.value:
	#		name = item.value
	#		if '.' not in name:
	#			name = name + '.sophia'
	#		module_routine = process(routine.namespace, module(name), link = True)
	#		module_routine.start()
	#		module_routine.proxy.bound = True
	#		routine.bind(item.value.split('.')[0], module_routine.proxy, sophia_process)

class else_statement(statement):

	def __init__(self, tokens):

		super().__init__(None)
		self.branch = True

	def execute(self, routine): # Final else statement
		
		return

class identifier(node): # Generic identifier class

	def __init__(self, tokens):

		super().__init__(tokens)
		self.lbp = 0

class literal(identifier): # Adds literal behaviours to a node

	def nud(self, lex):

		return self # Gives self as node

	def execute(self, routine): # Literal values are evaluated at parse time
		
		routine.send(self.value, self.type)

class name(identifier): # Adds name behaviours to a node

	def __init__(self, tokens):

		names = tokens.split('.')
		if names[0] in kadmos.sub_types: # Corrects shortened type names
			names[0] = kadmos.sub_types[names[0]]
		super().__init__(names[0])
		if len(names) > 1:
			self.operation = names[1]
		else:
			self.operation = None

	def nud(self, lex):

		if isinstance(lex.peek, left_bracket): # If function call:
			lex.use() # Gets the next token, which is guaranteed to be a left bracket
			return lex.token.led(lex, self) # Guaranteed to call the LED of the following left bracket
		else:
			return self # Gives self as node

	def execute(self, routine): # Terminal nodes

		if self.value in routine.types:
			type_name = routine.types[self.value]
		else:
			type_name = self.type
		value = routine.find(self.value)
		if self.operation:
			type_routine = routine.find(type_name)
			if isinstance(type_routine, type_statement):
				pass
			else:
				operation = getattr(type_routine, self.operation, None)
				if operation:
					routine.send(operation, 'function')
				else:
					return routine.error('Undefined type operation: ' + self.value)
		routine.send(value, type_name)

class keyword(identifier): # Adds keyword behaviours to a node

	def __init__(self, tokens):

		super().__init__(tokens)
		self.active = 0

	def nud(self, lex):

		return self

	def start(self, routine):

		loop = routine.node
		while not isinstance(loop, (while_statement, for_statement)): # Traverses up to closest enclosing loop - bootstrap assumes that interpreter is well-written and one exists
			loop = loop.head
			routine.path.pop()
		routine.node = loop
		if self.value == 'continue':
			if loop.value: # For loop
				if '.index' in routine.type_data: # Tests if loop is unbound
					loop.execute(routine)
				else:
					routine.branch(loop.length)
			else:
				routine.branch(0)
		elif self.value == 'break':
			routine.branch()
			if loop.value: # End for loop correctly
				routine.data.pop() # Don't check for type
				type_name = routine.type_data.pop()
				while type_name != '.index':
					routine.data.pop()
					type_name = routine.type_data.pop()
				routine.unbind(self.value.value)

	def execute(self, routine):

		return # Shouldn't ever be called anyway

class operator(node): # Generic operator node

	def __init__(self, value):

		super().__init__(value)
		self.lbp = kadmos.bp(value) # Gets binding power of symbol

class prefix(operator): # Adds prefix behaviours to a node

	def __init__(self, tokens):

		super().__init__(tokens)
		self.lbp = len(kadmos.binding_power) + 1 # Highest possible binding power

	def nud(self, lex):
		
		self.nodes = [lex.parse(self.lbp)]
		return self

	def execute(self, routine): # Unary operators

		op = routine.find(self.value) # Gets the operator definition
		x = routine.get(op.types[1])
		routine.send(op.unary(routine, x), op.types[0]) # Equivalent for all operators

class receive(prefix): # Defines the receive operator

	def nud(self, lex):

		self.value = lex.parse(self.lbp)
		return self

	def execute(self, routine):
		
		value = routine.messages.recv()
		if self.value.type:
			type_name = self.value.type
		else:
			type_name = None
		routine.bind(self.value.value, value, type_name)
		routine.send(value)

class resolve(prefix): # Defines the resolution operator

	def execute(self, routine):
		
		routine.message('dereference', routine.get('process'))
		routine.send(routine.calls.recv())

class infix(operator): # Adds infix behaviours to a node

	def led(self, lex, left):
		
		self.nodes = [left, lex.parse(self.lbp)]
		return self

	def execute(self, routine):
		
		op = routine.find(self.value) # Gets the operator definition
		x = routine.get(op.types[2])
		y = routine.get(op.types[1]) # Operands are received in reverse order
		routine.send(op.binary(routine, y, x), op.types[0])

class infix_r(operator): # Adds right-binding infix behaviours to a node

	def led(self, lex, left):
		
		self.nodes = [left, lex.parse(self.lbp - 1)]
		return self

	def execute(self, routine):

		if self.value == ':': # Sorts out list slices and key-item pairs by returning them as a slice object or a dictionary
			x = routine.get()
			y = routine.get()
			if self.nodes and self.nodes[1].value == ':':
				value = [y] + x
			else:
				value = [y, x]
			if self.head.value == ':':
				routine.send(value)
			else:
				if len(value) == 2:
					routine.send(arche.element(value))
				else:
					routine.send(arche.slice(value))
		elif self.value == ',': # Sorts out comma-separated parameters by returning them as a list
			x = routine.get()
			y = routine.get()
			if self.nodes and self.nodes[1].value == ',':
				value = [y] + x
			else:
				value = [y, x]
			routine.send(value)
		else: # Binary operators
			op = routine.find(self.value) # Gets the operator definition
			x = routine.get(op.types[2])
			y = routine.get(op.types[1])
			routine.send(op.binary(routine, y, x), op.types[0])

class bind(operator): # Defines the bind operator

	def __repr__(self):

		return 'bind ' + repr(self.value)

	def led(self, lex, left): # Parses like a binary operator but stores the left operand like assignment
		
		self.value, self.nodes = left, [lex.parse(self.lbp)]
		return self

	def execute(self, routine):
		
		routine.bind(self.value.value, routine.get('process'), 'process') # Binds routine

class send(operator): # Defines the send operator

	def __repr__(self):

		return 'send ' + repr(self.value)

	def led(self, lex, left): # Parses like a binary operator but stores the right operand like assignment
		
		self.nodes = [left, lex.parse(self.lbp)]
		return self

	def execute(self, routine):
		
		address = routine.get('process')
		value = routine.get()
		routine.message('transfer', address, value)

class left_bracket(operator): # Adds left-bracket behaviours to a node

	def nud(self, lex): # For normal parentheses
		
		if isinstance(lex.peek, right_bracket): # Empty brackets
			self.nodes = []
		else:
			self.nodes = [lex.parse(self.lbp)]
		lex.use()
		return self # The bracketed sub-expression as a whole is essentially a literal

	def led(self, lex, left): # For function calls
		
		if isinstance(lex.peek, right_bracket): # Empty brackets
			self.nodes = [left]
		else:
			self.nodes = [left, lex.parse(self.lbp)]
		lex.use()
		return self # The bracketed sub-expression as a whole is essentially a literal

class function_call(left_bracket):

	def execute(self, routine):

		if self.length > 1:
			args = routine.get()
			if not isinstance(args, list): # Type correction
				args = [args] # Very tiresome type correction, at that
		else:
			args = []
		if self.nodes[0].operation: # Type operation
			args = [routine.get()] + args # Shuffle arguments
		function = routine.get('function') # Get actual function
		if isinstance(function, function_statement):
			type_name = function.type
			if isinstance(self.head, bind):
				routine.message('spawn', function, args)
			else:
				routine.message('call', function, args)
			value = routine.calls.recv()
		else:
			type_name = None
			if args: # Yeah
				value = function(*args) # Since value is a Python function in this case
			else:
				value = function()
		routine.send(value, type_name)

class parenthesis(left_bracket):

	def execute(self, routine):

		return

class sequence_index(left_bracket):

	def execute(self, routine):
		
		subscript = routine.get()
		value = routine.get()
		if not isinstance(subscript, list):
			subscript = [subscript]
		for i in subscript: # Iteratively accesses the sequence
			if isinstance(i, arche.slice):
				if aletheia.sophia_sequence(value):
					if i.nodes[1] < -1 * len(value) or i.nodes[1] > len(value): # If out of bounds:
						return routine.error('Index out of bounds')
				else:
					return routine.error('Value not sliceable')
			elif aletheia.sophia_record(value):
				if i not in value:
					return routine.error('Key not in record: ' + i)
			else:
				if i < -1 * len(value) or i >= len(value): # If out of bounds:
					return routine.error('Index out of bounds')
			if aletheia.sophia_slice(i):
				if aletheia.sophia_string(value):
					value = ''.join([value[n] for n in i]) # Constructs slice of string using range
				elif aletheia.sophia_list(value):
					value = tuple([value[n] for n in i]) # Constructs slice of list using range
				elif aletheia.sophia_record(value):
					items = list(value.items())
					value = dict([items[n] for n in i]) # Constructs slice of record using range
			else:
				value = value[i] # Python can handle this bit
		routine.send(value) # Return the accessed value

class sequence_literal(left_bracket):

	def execute(self, routine):
		
		if self.nodes:
			items = routine.get()
		else:
			items = []
		if not isinstance(items, (list, arche.slice)):
			items = [items]
		if items and not isinstance(items, arche.slice) and isinstance(items[0], arche.element): # If items is a key-item pair in a record
			routine.send(dict(iter(items))) # Better way to merge a list of key-value pairs into a record
		else: # If list or slice:
			routine.send(tuple(items)) # Tuple expands slice

class meta_statement(left_bracket):

	def __init__(self, value):

		super().__init__(value)
		self.active = 1
		self.length = 2 # Becomes true at runtime

	def start(self, routine):
		
		data = routine.get('string')
		value = self.parse(data)
		hemera.debug_tree(value)

	def execute(self, routine):
		
		return

class right_bracket(operator): # Adds right-bracket behaviours to a node

	def __init__(self, value):

		super().__init__(value)

if __name__ == '__main__': # Supervisor process and pool management

	stream = mp.Queue() # Supervisor message stream
	events = globals() # Shortcut to access event handling functions

	def call(pid, routine, args):

		routine = task(routine, args)
		tasks[routine.pid] = kleio.proxy(routine)
		tasks[routine.pid].result = pool.apply_async(routine.execute)
		tasks[routine.pid].requests.append(pid) # Submit request for return value

	def spawn(pid, routine, args):

		routine = task(routine, args)
		tasks[routine.pid] = kleio.proxy(routine)
		tasks[routine.pid].result = pool.apply_async(routine.execute)
		tasks[routine.pid].references.append(pid) # Mark reference to process
		tasks[pid].calls.send(kleio.reference(routine.pid)) # Return reference to process

	def dereference(pid, routine):

		if tasks[routine.pid].result.ready():
			tasks[pid].calls.send(tasks[routine.pid].result.get())
		else:
			tasks[routine.pid].requests.append(pid) # Submit request for return value

	def transfer(pid, routine, message):

		tasks[routine.pid].messages.send(message)

	def terminate(pid):

		value = tasks[pid].result.get()
		for process in tasks[pid].requests:
			tasks[process].calls.send(value)
		if not tasks[pid].references: # Free task
			del tasks[pid]
		if pid == main.pid:
			stream.put(None) # End supervisor
	
	with mp.Pool(initializer = kleio.initialise, initargs = (stream,)) as pool: # Cheeky way to sneak a queue into a task
		
		pr = cProfile.Profile()
		pr.enable()
		main = task(module('test.sophia'), []) # Create initial task
		tasks = {main.pid: kleio.proxy(main)} # Proxies of tasks
		tasks[main.pid].result = pool.apply_async(main.execute) # Needs to be started after the proxy is created so that the pipes work
		while message := stream.get(): # Event listener pattern; runs until null sentinel value sent from unlinked module
			events[message[0]](*message[1:]) # Executes event
		else: 
			pr.disable()
			#pr.print_stats(sort = 'tottime')